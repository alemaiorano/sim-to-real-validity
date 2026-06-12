#!/usr/bin/env python3
"""Compare models from the pilot: for each data/predictions/*-pilot.jsonl, join with the
locked corpus CTR and compute within-package ranking validity (top-1, Kendall tau, Spearman
rho) with bootstrap CIs. Prints a comparison table and writes reports/pilot_model_comparison.json.

Decision rule (logged in METHODOLOGY.md): pick the CHEAPEST model whose validity CI overlaps
the best model's — i.e. statistically indistinguishable from the best.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
PRED_DIR = PAPER_DIR / "data" / "predictions"
REPORTS = PAPER_DIR / "reports"

# reuse the validated stats from compute_validity.py
spec = importlib.util.spec_from_file_location("cv", PAPER_DIR / "scripts" / "compute_validity.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)


def latest_corpus_ctr() -> dict[tuple[str, str], float]:
    cands = [c for c in sorted(DATASETS.glob("upworthy-subset-*.json"))
             if not c.name.endswith(".manifest.json")]
    if not cands:
        print("[pilot] no corpus", file=sys.stderr); sys.exit(1)
    corpus = json.loads(cands[-1].read_text())
    return {(p["package_id"], v["variant_id"]): v["real_ctr"]
            for p in corpus for v in p["variants"]}


def analyze(pred_file: Path, ctr: dict) -> dict:
    pkgs: dict[str, list[tuple[float, float]]] = {}
    with pred_file.open() as fh:
        for line in fh:
            r = json.loads(line)
            key = (r["package_id"], r["variant_id"])
            if key in ctr:
                pkgs.setdefault(r["package_id"], []).append((ctr[key], float(r["pred_score"])))
    pkgs = {k: v for k, v in pkgs.items() if len(v) >= 2}
    taus, rhos, hits = [], [], []
    for variants in pkgs.values():
        real = [x[0] for x in variants]; pred = [x[1] for x in variants]
        t = cv.kendall_tau(real, pred); s = cv.spearman(real, pred)
        if t is not None: taus.append(t)
        if s is not None: rhos.append(s)
        hits.append(cv.top1(real, pred))
    n = len(pkgs)
    return {
        "n_packages": n,
        "kendall_tau": {"mean": sum(taus)/len(taus), "ci95": cv.bootstrap_ci(taus)},
        "spearman_rho": {"mean": sum(rhos)/len(rhos), "ci95": cv.bootstrap_ci(rhos)},
        "top1_accuracy": {"mean": sum(hits)/len(hits), "ci95": cv.bootstrap_ci([float(h) for h in hits])},
        "random_top1_baseline": sum(1.0/len(v) for v in pkgs.values())/n,
    }


def main() -> None:
    ctr = latest_corpus_ctr()
    files = sorted(PRED_DIR.glob("*-pilot.jsonl"))
    if not files:
        print("[pilot] no *-pilot.jsonl in data/predictions/", file=sys.stderr); sys.exit(1)
    out = {}
    print(f"{'model':28} {'n':>3} {'top1':>16} {'tau':>16} {'rho':>16}  rand")
    for f in files:
        model = f.stem.replace("-pilot", "").replace("_", ".")
        r = analyze(f, ctr); out[model] = r
        def fmt(d): return f"{d['mean']:.3f}[{d['ci95'][0]:.2f},{d['ci95'][1]:.2f}]"
        print(f"{model:28} {r['n_packages']:>3} {fmt(r['top1_accuracy']):>16} "
              f"{fmt(r['kendall_tau']):>16} {fmt(r['spearman_rho']):>16}  {r['random_top1_baseline']:.2f}")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "pilot_model_comparison.json").write_text(json.dumps(out, indent=2))
    print(f"\n[pilot] wrote reports/pilot_model_comparison.json")


if __name__ == "__main__":
    main()
