#!/usr/bin/env python3
"""Descriptive disagreement diagnostics; spread does not identify a mechanism."""
import argparse
import json
import statistics
from pathlib import Path
from analysis_io import write_json
from analyze_replication import load, packages
import compute_validity as cv
from winner_filter import POLICY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text())
    panel, eligible = packages(corpus, load(args.panel))
    baseline, _ = packages(corpus, load(args.baseline))
    shared = sorted(panel.keys() & baseline.keys())
    spreads = {"panel": [], "baseline": []}
    examples = []
    for key in shared:
        real = [v[0] for v in panel[key]]
        pp, bp = [v[1] for v in panel[key]], [v[1] for v in baseline[key]]
        spreads["panel"].append(statistics.pstdev(pp))
        spreads["baseline"].append(statistics.pstdev(bp))
        if cv.top1(real, bp) > cv.top1(real, pp):
            examples.append({"package_id": key, "panel_expected_top1": cv.top1(real, pp),
                             "baseline_expected_top1": cv.top1(real, bp)})
    write_json(args.output, {"winner_filter_policy": POLICY, "n_eligible": eligible,
                            "n_paired": len(shared), "mean_within_package_sd": {
                                arm: statistics.mean(vals) if vals else None for arm, vals in spreads.items()},
                            "interpretation": "descriptive spread only; does not distinguish bias from noise",
                            "baseline_higher_expected_top1": examples})


if __name__ == "__main__":
    main()
