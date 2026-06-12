#!/usr/bin/env python3
"""Qualitative/quantitative error analysis (RQ: why do personas hurt?).

Uses existing artifacts (persona = data/sim_predictions.jsonl, baseline =
data/predictions/gemini-3_1-flash-lite-baseline.jsonl, corpus). Computes:
  (1) discriminativeness: mean within-package SD of pred_score for baseline vs persona
      (if personas compress scores, they wash out signal -> caricature/averaging effect);
  (2) example packages where the baseline ranks the real winner #1 but the persona panel does not,
      for a qualitative supplementary table.
Outputs reports/error_analysis.json.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"


def load(path: Path) -> dict:
    d = {}
    for line in path.open():
        r = json.loads(line)
        d[(r["package_id"], r["variant_id"])] = float(r["pred_score"])
    return d


def main() -> None:
    corpus = json.loads(next(c for c in sorted(DATASETS.glob("upworthy-subset-*.json"))
                             if not c.name.endswith(".manifest.json")).read_text())
    sig = [p for p in corpus if p.get("winner_significant")]
    persona = load(PAPER_DIR / "data" / "sim_predictions.jsonl")
    base = load(PAPER_DIR / "data" / "predictions" / "gemini-3_1-flash-lite-baseline.jsonl")

    base_sd, persona_sd = [], []
    examples = []
    for pkg in sig:
        keys = [(pkg["package_id"], v["variant_id"]) for v in pkg["variants"]]
        if not (all(k in persona for k in keys) and all(k in base for k in keys)):
            continue
        real = [v["real_ctr"] for v in pkg["variants"]]
        bp = [base[k] for k in keys]
        pp = [persona[k] for k in keys]
        if len(real) < 2:
            continue
        base_sd.append(statistics.pstdev(bp))
        persona_sd.append(statistics.pstdev(pp))
        # example: baseline picks real winner, persona does not
        real_best = max(range(len(real)), key=lambda i: real[i])
        if (max(range(len(bp)), key=lambda i: bp[i]) == real_best
                and max(range(len(pp)), key=lambda i: pp[i]) != real_best):
            examples.append({
                "package_id": pkg["package_id"],
                "winner_headline": pkg["variants"][real_best]["headline"][:90],
                "winner_real_ctr": round(real[real_best], 4),
                "n_variants": len(real),
            })

    report = {
        "n_packages": len(base_sd),
        "discriminativeness_within_pkg_sd": {
            "baseline_mean_sd": round(statistics.mean(base_sd), 4),
            "persona_mean_sd": round(statistics.mean(persona_sd), 4),
            "interpretation": "lower SD = scores compressed = less discriminative",
        },
        "n_baseline_right_persona_wrong": len(examples),
        "examples": examples[:15],
    }
    (PAPER_DIR / "reports" / "error_analysis.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2)[:1200])


if __name__ == "__main__":
    main()
