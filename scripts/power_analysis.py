#!/usr/bin/env python3
"""A-priori power analysis for the sim-to-real study, to justify sample sizes against the
risk of an under-powered-study critique. Effect-size thresholds follow Cohen (1988).

Outputs reports/power_analysis.json. Two claims:
  (1) rank correlation (Kendall tau / Spearman rho), package = inferential unit;
  (2) top-1 winner accuracy vs the random baseline (one-sample proportion).

Required n via:
  - correlation: Fisher z, n = ((z_a/2 + z_b)/atanh(r))^2 + 3
  - proportion : n = (z_a/2*sqrt(p0 q0) + z_b*sqrt(p1 q1))^2 / (p1-p0)^2
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
RAW = PAPER_DIR / "data" / "upworthy_raw" / "upworthy-exploratory.csv"
REPORTS = PAPER_DIR / "reports"

Z_A = 1.959963985   # two-sided alpha=0.05
Z_B = 0.841621234   # power=0.80


def n_for_correlation(r: float) -> int:
    return math.ceil((( Z_A + Z_B) / math.atanh(r)) ** 2 + 3)


def n_for_proportion(p0: float, p1: float) -> int:
    num = (Z_A * math.sqrt(p0 * (1 - p0)) + Z_B * math.sqrt(p1 * (1 - p1))) ** 2
    return math.ceil(num / (p1 - p0) ** 2)


def count_eligible_significant() -> dict:
    """Replicate the ingest filters on the raw CSV and count significant-winner packages,
    to know how many reliable packages the full eligible pool can supply."""
    if not RAW.exists():
        return {"note": "raw CSV not present; skipped eligible count"}
    agg: dict[str, dict[str, dict[str, int]]] = {}
    with RAW.open() as fh:
        for r in csv.DictReader(fh):
            try:
                imp, clk = int(r["impressions"]), int(r["clicks"])
            except (ValueError, KeyError):
                continue
            h = r["headline"].strip()
            if not h:
                continue
            cell = agg.setdefault(r["clickability_test_id"].strip(), {}).setdefault(h, {"i": 0, "c": 0})
            cell["i"] += imp; cell["c"] += clk

    def p_one(c1, n1, c2, n2):
        p = (c1 + c2) / (n1 + n2)
        se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
        if se == 0:
            return 1.0
        z = (c1 / n1 - c2 / n2) / se
        return 0.5 * (1 - math.erf(z / math.sqrt(2)))

    eligible = sig = 0
    for hs in agg.values():
        variants = [(d["c"], d["i"]) for d in hs.values() if d["i"] >= 3000]
        if len(variants) < 2:
            continue
        eligible += 1
        variants.sort(key=lambda x: -(x[0] / x[1]))
        (c1, n1), (c2, n2) = variants[0], variants[1]
        if p_one(c1, n1, c2, n2) < 0.05:
            sig += 1
    return {"eligible_packages": eligible, "significant_winner_packages": sig,
            "significant_rate": round(sig / eligible, 3) if eligible else None}


def main() -> None:
    report = {
        "alpha": 0.05, "power": 0.80,
        "effect_thresholds_cohen1988": {"small": 0.1, "medium": 0.3, "large": 0.5},
        "n_required_correlation": {f"r={r}": n_for_correlation(r) for r in (0.10, 0.15, 0.20, 0.30)},
        "n_required_top1_vs_baseline": {
            "p0=0.312,p1=0.363 (observed +5.1pp)": n_for_proportion(0.312, 0.363),
            "p0=0.312,p1=0.412 (+10pp)": n_for_proportion(0.312, 0.412),
            "p0=0.312,p1=0.462 (+15pp)": n_for_proportion(0.312, 0.462),
        },
        "current_primary_n_significant": 124,
        "available_in_full_eligible_pool": count_eligible_significant(),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "power_analysis.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
