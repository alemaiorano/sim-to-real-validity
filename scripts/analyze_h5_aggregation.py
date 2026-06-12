#!/usr/bin/env python3
"""H5 — does a smarter aggregation rule recover persona-panel validity?

The primary result (compute_validity.py) aggregates the panel with a plain ARITHMETIC
MEAN over all persona x draw observations per variant, giving Kendall tau ~= 0.084 and
top-1 ~= 34.6% on the n=399 reliable-winner Upworthy packages -- well below the no-persona
baseline (tau ~= 0.361, top-1 ~= 49.2%). The paper flags "single aggregation rule" as an
untested design choice. This script tests alternatives on the SAME per-persona observations,
so it requires NO new API calls.

Per-persona raw scores live in the resumable checkpoint written by run_predictions.py:
  data/predictions/.checkpoint-gemini-3_1-flash-lite-sig3.jsonl
  (399 reliable-winner packages x 10 personas x 3 draws = 44,782 observations)
Ground-truth CTR + reliable-winner flag come from data/joined.csv.

Aggregation rules compared (all WITHIN package, the only audience-comparable unit):
  mean        panel arithmetic mean over persona x draw  (reproduces the paper's number)
  median      panel median (robust to per-persona outliers)
  trimmed20   10% trimmed mean each tail (disagreement-aware, drops extremes)
  zmean       per-persona z-score across the package's variants, then mean
              (removes per-persona scale/level bias before pooling)
  borda       rank fusion: each persona ranks the variants, sum ranks (Borda count)
  condorcet   pairwise majority (Copeland): variant score = #pairwise wins across personas

Writes reports/h5_aggregation.json and reports/h5_aggregation.csv. The no-persona baseline
and the published panel-mean are reported as reference rows. Fails loudly if inputs absent.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
JOINED = PAPER_DIR / "data" / "joined.csv"
PRED = PAPER_DIR / "data" / "predictions"
CKPT = PRED / ".checkpoint-gemini-3_1-flash-lite-sig3.jsonl"
BASELINE = PRED / "gemini-3_1-flash-lite-baseline.jsonl"
REPORTS = PAPER_DIR / "reports"

spec = importlib.util.spec_from_file_location("cv", PAPER_DIR / "scripts" / "compute_validity.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)  # reuse kendall_tau / spearman / top1 / bottom1 / bootstrap_ci


def fail(msg: str) -> None:
    print(f"[h5][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def load_ground_truth() -> dict[str, dict[str, float]]:
    """significant-winner packages only -> {package_id: {variant_id: real_ctr}}."""
    if not JOINED.exists():
        fail(f"missing {JOINED}; run 03_build_joined.py")
    gt: dict[str, dict[str, float]] = defaultdict(dict)
    for r in csv.DictReader(JOINED.open()):
        if int(r.get("winner_significant", 0)):
            gt[r["package_id"]][r["variant_id"]] = float(r["real_ctr"])
    return {k: v for k, v in gt.items() if len(v) >= 2}


def load_per_persona() -> dict[str, dict[str, dict[str, float]]]:
    """checkpoint -> {package: {variant: {persona: mean-over-draws score}}}."""
    if not CKPT.exists():
        fail(f"missing per-persona checkpoint {CKPT}")
    raw: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for line in CKPT.open():
        if not line.strip():
            continue
        r = json.loads(line)
        raw[(r["package_id"], r["variant_id"], r["persona_id"])].append(float(r["value"]))
    out: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for (pkg, var, persona), vals in raw.items():
        out[pkg][var][persona] = sum(vals) / len(vals)
    return out


def load_baseline_pred() -> dict[str, dict[str, float]]:
    """no-persona baseline final preds -> {package: {variant: pred_score}}."""
    if not BASELINE.exists():
        fail(f"missing baseline preds {BASELINE}")
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for line in BASELINE.open():
        r = json.loads(line)
        out[r["package_id"]][r["variant_id"]] = float(r["pred_score"])
    return out


# ---- aggregation rules: dict[persona -> score] over variants of one package -> dict[variant -> score]

def _trimmed_mean(xs: list[float], frac: float = 0.1) -> float:
    xs = sorted(xs)
    k = int(len(xs) * frac)
    core = xs[k: len(xs) - k] or xs
    return sum(core) / len(core)


def agg_level(per_persona: dict[str, dict[str, float]], how: str) -> dict[str, float]:
    """Level-based rules: pool persona scores per variant, then reduce."""
    out = {}
    for var, pmap in per_persona.items():
        vals = list(pmap.values())
        if how == "mean":
            out[var] = sum(vals) / len(vals)
        elif how == "median":
            out[var] = statistics.median(vals)
        elif how == "trimmed20":
            out[var] = _trimmed_mean(vals, 0.1)
        else:
            raise ValueError(how)
    return out


def agg_zmean(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """z-score each persona ACROSS the package's variants, then mean across personas.
    Removes per-persona scale/offset (a persona who rates everything high adds no signal)."""
    variants = list(per_persona.keys())
    # rebuild as persona -> {variant: score}
    by_persona: dict[str, dict[str, float]] = defaultdict(dict)
    for var, pmap in per_persona.items():
        for persona, s in pmap.items():
            by_persona[persona][var] = s
    contrib: dict[str, list[float]] = defaultdict(list)
    for persona, vmap in by_persona.items():
        if len(vmap) < len(variants):  # persona must score every variant to contribute
            continue
        vals = list(vmap.values())
        mu = sum(vals) / len(vals)
        sd = statistics.pstdev(vals)
        for var, s in vmap.items():
            contrib[var].append((s - mu) / sd if sd > 0 else 0.0)
    return {var: (sum(cs) / len(cs) if cs else 0.0) for var, cs in
            ((v, contrib.get(v, [])) for v in variants)}


def _persona_ballots(per_persona: dict[str, dict[str, float]]) -> tuple[list[str], list[dict[str, float]]]:
    """variants + list of per-persona {variant: score}, keeping only personas that scored all."""
    variants = list(per_persona.keys())
    by_persona: dict[str, dict[str, float]] = defaultdict(dict)
    for var, pmap in per_persona.items():
        for persona, s in pmap.items():
            by_persona[persona][var] = s
    ballots = [vmap for vmap in by_persona.values() if len(vmap) == len(variants)]
    return variants, ballots


def agg_borda(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """Rank fusion: each persona ranks variants; Borda points summed (ties share avg points)."""
    variants, ballots = _persona_ballots(per_persona)
    score = {v: 0.0 for v in variants}
    for vmap in ballots:
        ranks = cv._ranks([vmap[v] for v in variants])  # 1=lowest score
        for v, rk in zip(variants, ranks):
            score[v] += rk  # higher rank (higher score) -> more Borda points
    return score


def agg_condorcet(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """Copeland: for each ordered pair, count personas preferring it; variant score = #pairwise wins."""
    variants, ballots = _persona_ballots(per_persona)
    wins = {v: 0.0 for v in variants}
    for i in range(len(variants)):
        for j in range(i + 1, len(variants)):
            a, b = variants[i], variants[j]
            pa = sum(1 for vm in ballots if vm[a] > vm[b])
            pb = sum(1 for vm in ballots if vm[b] > vm[a])
            if pa > pb:
                wins[a] += 1
            elif pb > pa:
                wins[b] += 1
            else:
                wins[a] += 0.5
                wins[b] += 0.5
    return wins


RULES = {
    "mean": lambda pp: agg_level(pp, "mean"),
    "median": lambda pp: agg_level(pp, "median"),
    "trimmed20": lambda pp: agg_level(pp, "trimmed20"),
    "zmean": agg_zmean,
    "borda": agg_borda,
    "condorcet": agg_condorcet,
}


def evaluate(gt: dict[str, dict[str, float]],
             pred_by_pkg: dict[str, dict[str, float]]) -> dict:
    """compute_validity-style metrics over packages with full prediction coverage."""
    taus, rhos, hits, lifts = [], [], [], []
    n = 0
    for pkg, real_map in gt.items():
        pred_map = pred_by_pkg.get(pkg)
        if not pred_map or not all(v in pred_map for v in real_map):
            continue
        n += 1
        variants = list(real_map.keys())
        real = [real_map[v] for v in variants]
        pred = [pred_map[v] for v in variants]
        t = cv.kendall_tau(real, pred)
        s = cv.spearman(real, pred)
        if t is not None:
            taus.append(t)
        if s is not None:
            rhos.append(s)
        hits.append(cv.top1(real, pred))
        best, worst = max(real), min(real)
        if best > worst:
            picked = real[max(range(len(pred)), key=lambda i: pred[i])]
            lifts.append((picked - worst) / (best - worst))
    return {
        "n_packages": n,
        "kendall_tau": {"mean": sum(taus) / len(taus), "ci95": cv.bootstrap_ci(taus)},
        "spearman_rho": {"mean": sum(rhos) / len(rhos), "ci95": cv.bootstrap_ci(rhos)},
        "top1_accuracy": {"mean": sum(hits) / len(hits),
                          "ci95": cv.bootstrap_ci([float(h) for h in hits])},
        "lift_captured": {"mean": sum(lifts) / len(lifts), "ci95": cv.bootstrap_ci(lifts)},
    }


def main() -> None:
    gt = load_ground_truth()
    per_persona = load_per_persona()
    baseline = load_baseline_pred()

    results: dict[str, dict] = {}

    # reference: no-persona baseline on the same reliable-winner packages
    results["baseline_no_persona"] = evaluate(gt, baseline)

    # each persona aggregation rule
    for name, fn in RULES.items():
        pred_by_pkg = {pkg: fn(pp) for pkg, pp in per_persona.items()}
        results[name] = evaluate(gt, pred_by_pkg)

    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "_doc": "H5: alternative persona aggregation rules vs panel mean and no-persona baseline. "
                "Same per-persona observations as the primary result; no new API calls.",
        "source_checkpoint": CKPT.name,
        "n_reliable_winner_packages": len(gt),
        "results": results,
    }
    (REPORTS / "h5_aggregation.json").write_text(json.dumps(payload, indent=2))

    # flat CSV for the paper table
    with (REPORTS / "h5_aggregation.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rule", "n", "kendall_tau", "tau_lo", "tau_hi",
                    "top1", "top1_lo", "top1_hi", "lift", "lift_lo", "lift_hi"])
        order = ["baseline_no_persona", "mean", "median", "trimmed20", "zmean", "borda", "condorcet"]
        for name in order:
            r = results[name]
            w.writerow([name, r["n_packages"],
                        f"{r['kendall_tau']['mean']:.3f}", f"{r['kendall_tau']['ci95'][0]:.3f}",
                        f"{r['kendall_tau']['ci95'][1]:.3f}",
                        f"{r['top1_accuracy']['mean']:.3f}", f"{r['top1_accuracy']['ci95'][0]:.3f}",
                        f"{r['top1_accuracy']['ci95'][1]:.3f}",
                        f"{r['lift_captured']['mean']:.3f}", f"{r['lift_captured']['ci95'][0]:.3f}",
                        f"{r['lift_captured']['ci95'][1]:.3f}"])

    # console summary
    print(f"[h5] n={len(gt)} reliable-winner packages | metrics with 95% bootstrap CI\n")
    print(f"{'rule':<20} {'kendall_tau':>22} {'top1':>20}")
    for name in ["baseline_no_persona", "mean", "median", "trimmed20", "zmean", "borda", "condorcet"]:
        r = results[name]
        t, tc = r["kendall_tau"]["mean"], r["kendall_tau"]["ci95"]
        h, hc = r["top1_accuracy"]["mean"], r["top1_accuracy"]["ci95"]
        print(f"{name:<20} {t:>7.3f} [{tc[0]:.3f},{tc[1]:.3f}] {h:>9.3f} [{hc[0]:.3f},{hc[1]:.3f}]")
    print("\nwrote reports/h5_aggregation.json + reports/h5_aggregation.csv")


if __name__ == "__main__":
    main()
