#!/usr/bin/env python3
"""Compute within-package ranking validity from data/joined.csv.

Outputs reports/correlation.json (RQ1) and reports/construct_validity.json (RQ2).
All ranking is WITHIN package, since Upworthy variants share an audience only
within a package (see README construct-validity note). Package-level scores are
aggregated with a percentile bootstrap CI over packages.

No SciPy dependency: Spearman/Kendall/top-1 are computed directly. Fails loudly
if joined.csv is absent.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
JOINED = PAPER_DIR / "data" / "joined.csv"
REPORTS = PAPER_DIR / "reports"
BOOTSTRAP_ITERS = 10000
SEED = 42


def fail(msg: str) -> None:
    print(f"[validity][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def load_packages(significant_only: bool = False) -> dict[str, list[tuple[float, float]]]:
    if not JOINED.exists():
        fail(f"joined artifact missing: {JOINED}; run 03_build_joined.py first")
    pkgs: dict[str, list[tuple[float, float]]] = {}
    with JOINED.open() as fh:
        for r in csv.DictReader(fh):
            if significant_only and not int(r.get("winner_significant", 0)):
                continue
            pkgs.setdefault(r["package_id"], []).append(
                (float(r["real_ctr"]), float(r["pred_score"]))
            )
    return {k: v for k, v in pkgs.items() if len(v) >= 2}


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    if n < 2:
        return None
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    return num / (da * db) if da and db else None


def kendall_tau(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    if n < 2:
        return None
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (a[i] - a[j]) * (b[i] - b[j])
            if s > 0:
                conc += 1
            elif s < 0:
                disc += 1
    denom = conc + disc
    return (conc - disc) / denom if denom else None


def top1(real: list[float], pred: list[float]) -> int:
    real_best = max(range(len(real)), key=lambda i: real[i])
    pred_best = max(range(len(pred)), key=lambda i: pred[i])
    return 1 if real_best == pred_best else 0


def bottom1(real: list[float], pred: list[float]) -> int:
    real_worst = min(range(len(real)), key=lambda i: real[i])
    pred_worst = min(range(len(pred)), key=lambda i: pred[i])
    return 1 if real_worst == pred_worst else 0


def bootstrap_ci(values: list[float], iters: int = BOOTSTRAP_ITERS) -> list[float]:
    rnd = random.Random(SEED)
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[rnd.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * iters)]
    hi = means[int(0.975 * iters)]
    return [lo, hi]


def analyze(pkgs: dict[str, list[tuple[float, float]]]) -> dict:
    taus, rhos, hits, lows, lifts = [], [], [], [], []
    for variants in pkgs.values():
        real = [x[0] for x in variants]
        pred = [x[1] for x in variants]
        t = kendall_tau(real, pred)
        s = spearman(real, pred)
        if t is not None:
            taus.append(t)
        if s is not None:
            rhos.append(s)
        hits.append(top1(real, pred))
        lows.append(bottom1(real, pred))
        # decision-relevant metric: fraction of achievable CTR lift captured by the top-1 pick
        # (0 = picks the worst variant, 1 = picks the real best). Cf. realized reward in A/B/bandit.
        best, worst = max(real), min(real)
        if best > worst:
            picked = real[max(range(len(pred)), key=lambda i: pred[i])]
            lifts.append((picked - worst) / (best - worst))
    n_pkg = len(pkgs)
    return {
        "n_packages": n_pkg,
        "n_variants": sum(len(v) for v in pkgs.values()),
        "kendall_tau": {"mean": sum(taus) / len(taus), "ci95": bootstrap_ci(taus)},
        "spearman_rho": {"mean": sum(rhos) / len(rhos), "ci95": bootstrap_ci(rhos)},
        "top1_accuracy": {"mean": sum(hits) / len(hits), "ci95": bootstrap_ci([float(h) for h in hits])},
        "bottom1_accuracy": {"mean": sum(lows) / len(lows), "ci95": bootstrap_ci([float(h) for h in lows])},
        "lift_captured": {"mean": sum(lifts) / len(lifts), "ci95": bootstrap_ci(lifts)},
        "random_top1_baseline": sum(1.0 / len(v) for v in pkgs.values()) / n_pkg,
    }


def main() -> None:
    # PRIMARY analysis = packages with a statistically significant ground-truth winner
    # (reliable label; kohavi2009controlled). SENSITIVITY = all predicted packages.
    primary = load_packages(significant_only=True)
    if not primary:
        fail("no significant-winner packages with >= 2 variants in joined.csv")
    out = {
        "primary_significant_winner": analyze(primary),
        "sensitivity_all_predicted": analyze(load_packages(significant_only=False)),
        "_note": "Primary = significant-winner packages (reliable ground truth). "
                 "Sensitivity = all predicted packages (includes noisy labels).",
    }
    # keep top-level keys for the variable/table generators (point them at the primary result)
    out.update(out["primary_significant_winner"])

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "correlation.json").write_text(json.dumps(out, indent=2))
    p = out["primary_significant_winner"]
    print(f"[validity] PRIMARY n={p['n_packages']}: tau={p['kendall_tau']['mean']:.3f} "
          f"CI{p['kendall_tau']['ci95']}, top1={p['top1_accuracy']['mean']:.3f} "
          f"vs random {p['random_top1_baseline']:.3f}")


if __name__ == "__main__":
    main()
