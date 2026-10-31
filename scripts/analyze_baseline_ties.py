#!/usr/bin/env python3
"""Exact-score tie diagnostics; no rounded score is treated as an exact tie."""
import argparse
import json
from pathlib import Path
from analysis_io import write_json
from analyze_replication import load, packages
import compute_validity as cv
from winner_filter import POLICY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    values, eligible = packages(json.loads(args.corpus.read_text()), load(args.predictions))
    all_tied = partial_top = 0
    for variants in values.values():
        scores = [x[1] for x in variants]
        all_tied += len(set(scores)) == 1
        partial_top += 1 < sum(s == max(scores) for s in scores) < len(scores)
    write_json(args.output, {"winner_filter_policy": POLICY, "n_eligible": eligible,
                            "n_packages": len(values), "score_equality": "exact",
                            "all_tied_packages": all_tied, "partial_top_tie_packages": partial_top,
                            "metrics": cv.analyze(values)})


if __name__ == "__main__":
    main()
