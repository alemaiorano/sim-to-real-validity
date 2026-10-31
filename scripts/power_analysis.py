#!/usr/bin/env python3
"""Historical planning formulas, not power for mean within-package concordance.
Fisher-z is for one correlation; the proportion calculation uses planning assumptions.
Writes an explicitly scoped new report, never the published power artifact.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import argparse
from analysis_io import write_json

Z_A = 1.959963985   # two-sided alpha=0.05
Z_B = 0.841621234   # power=0.80


def n_for_correlation(r: float) -> int:
    return math.ceil((( Z_A + Z_B) / math.atanh(r)) ** 2 + 3)


def n_for_proportion(p0: float, p1: float) -> int:
    num = (Z_A * math.sqrt(p0 * (1 - p0)) + Z_B * math.sqrt(p1 * (1 - p1))) ** 2
    return math.ceil(num / (p1 - p0) ** 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "status": "historical_planning_only_not_power_for_mean_package_concordance",
        "alpha": 0.05, "power": 0.80,
        "effect_thresholds_cohen1988": {"small": 0.1, "medium": 0.3, "large": 0.5},
        "n_required_correlation": {f"r={r}": n_for_correlation(r) for r in (0.10, 0.15, 0.20, 0.30)},
        "n_required_top1_vs_baseline": {
            "p0=0.312,p1=0.363 (planning +5.1pp)": n_for_proportion(0.312, 0.363),
            "p0=0.312,p1=0.412 (+10pp)": n_for_proportion(0.312, 0.412),
            "p0=0.312,p1=0.462 (+15pp)": n_for_proportion(0.312, 0.462),
        },
        "historical_planning_n": 124,
        "available_in_full_eligible_pool": {"status": "not_recomputed_by_planning_script"},
    }
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
