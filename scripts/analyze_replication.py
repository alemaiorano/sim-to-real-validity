#!/usr/bin/env python3
"""Cross-dataset replication analysis. For each dataset (corpus + persona preds + baseline preds),
compute within-package validity (Kendall tau, top-1) for the persona panel and the no-persona
baseline on the significant-winner packages. Writes reports/replication.json.

Usage: python scripts/analyze_replication.py
  (auto-discovers the configured datasets below; skips any whose prediction files are missing)
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
PRED = PAPER_DIR / "data" / "predictions"
spec = importlib.util.spec_from_file_location("cv", PAPER_DIR / "scripts" / "compute_validity.py")
cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)

# dataset label -> (corpus json, persona preds, baseline preds)
DSETS = {
    "exploratory": ("upworthy-subset-2026-06-03.json",
                    "gemini-3_1-flash-lite-full.jsonl", "gemini-3_1-flash-lite-baseline.jsonl"),
    "holdout": ("upworthy-holdout-2026-06-03.json",
                "gemini-3_1-flash-lite-hoP.jsonl", "gemini-3_1-flash-lite-hoB.jsonl"),
    "confirmatory": ("upworthy-confirmatory-2026-06-03.json",
                     "gemini-3_1-flash-lite-coP.jsonl", "gemini-3_1-flash-lite-coB.jsonl"),
    "mind-news": ("mind-subset-2026-06-03.json",
                  "gemini-3_1-flash-lite-mindP.jsonl", "gemini-3_1-flash-lite-mindB.jsonl"),
    "reddit-titles": ("reddit-subset-2026-06-04.json",
                      "gemini-3_1-flash-lite-redP.jsonl", "gemini-3_1-flash-lite-redB.jsonl"),
}


def load(p: Path) -> dict:
    d = {}
    for line in p.open():
        r = json.loads(line); d[(r["package_id"], r["variant_id"])] = float(r["pred_score"])
    return d


def metrics(corpus, preds):
    sig = {p["package_id"] for p in corpus if p.get("winner_significant")}
    # Require FULL coverage per package (all variants predicted) — matches 03_build_joined,
    # so a few LLM parse-misses can't leave a partially-ranked package biasing the metrics.
    pk = {}
    for p in corpus:
        if p["package_id"] not in sig:
            continue
        keys = [(p["package_id"], v["variant_id"]) for v in p["variants"]]
        if len(keys) < 2 or not all(k in preds for k in keys):
            continue
        pk[p["package_id"]] = [(v["real_ctr"], preds[(p["package_id"], v["variant_id"])])
                               for v in p["variants"]]
    taus, hits, lifts = [], [], []
    for vs in pk.values():
        r = [x[0] for x in vs]; p = [x[1] for x in vs]
        t = cv.kendall_tau(r, p)
        if t is not None:
            taus.append(t)
        hits.append(cv.top1(r, p))
        best, worst = max(r), min(r)
        if best > worst:
            picked = r[max(range(len(p)), key=lambda i: p[i])]
            lifts.append((picked - worst) / (best - worst))
    return {"n": len(pk),
            "kendall_tau": {"mean": sum(taus)/len(taus), "ci95": cv.bootstrap_ci(taus)},
            "top1": {"mean": sum(hits)/len(hits), "ci95": cv.bootstrap_ci([float(h) for h in hits])},
            "lift_captured": {"mean": sum(lifts)/len(lifts), "ci95": cv.bootstrap_ci(lifts)}}


def main() -> None:
    out = {}
    for label, (corp, pf, bf) in DSETS.items():
        cp, pp, bp = DATASETS / corp, PRED / pf, PRED / bf
        if not (cp.exists() and pp.exists() and bp.exists()):
            print(f"[replication] SKIP {label} (missing files)")
            continue
        corpus = json.loads(cp.read_text())
        out[label] = {"persona": metrics(corpus, load(pp)), "baseline": metrics(corpus, load(bp))}
        p, b = out[label]["persona"], out[label]["baseline"]
        print(f"{label:13} n={p['n']:5} | persona tau={p['kendall_tau']['mean']:.3f} "
              f"top1={p['top1']['mean']:.3f} || baseline tau={b['kendall_tau']['mean']:.3f} "
              f"top1={b['top1']['mean']:.3f} | gap_tau=+{b['kendall_tau']['mean']-p['kendall_tau']['mean']:.3f}")
    (PAPER_DIR / "reports" / "replication.json").write_text(json.dumps(out, indent=2))
    print("wrote reports/replication.json")


if __name__ == "__main__":
    main()
