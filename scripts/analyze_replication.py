#!/usr/bin/env python3
"""Corrected, counts-filtered analyses on explicit corpus and prediction files."""
import argparse
import json
from pathlib import Path
from analysis_io import write_json
import compute_validity as cv
from winner_filter import evaluate_winner, POLICY
import importlib.util

_spec = importlib.util.spec_from_file_location("joined_inputs", Path(__file__).with_name("03_build_joined.py"))
_join = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_join)
load = _join.load_predictions


def packages(corpus, predictions):
    result = {}
    eligible = 0
    for package in corpus:
        if not evaluate_winner(package["variants"])["selected"]:
            continue
        eligible += 1
        keys = [(package["package_id"], v["variant_id"]) for v in package["variants"]]
        if not all(key in predictions for key in keys):
            continue
        result[package["package_id"]] = [(v["real_ctr"], predictions[key]) for v, key in zip(package["variants"], keys)]
    return result, eligible


def metrics(corpus, predictions, iters=cv.BOOTSTRAP_ITERS):
    values, eligible = packages(corpus, predictions)
    return {"n_eligible": eligible, "n_missing_prediction_coverage": eligible - len(values), **cv.analyze(values, iters)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text())
    panel, baseline = load(args.panel), load(args.baseline)
    panel_pkgs, eligible = packages(corpus, panel)
    baseline_pkgs, _ = packages(corpus, baseline)
    write_json(args.output, {"analysis_schema": cv.METRIC_POLICY, "winner_filter_policy": POLICY,
                            "n_eligible": eligible, "panel": metrics(corpus, panel),
                            "baseline": metrics(corpus, baseline),
                            "paired_gap": cv.paired_analysis(panel_pkgs, baseline_pkgs)})


if __name__ == "__main__":
    main()
