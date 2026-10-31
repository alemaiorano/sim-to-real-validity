#!/usr/bin/env python3
"""RQ2 on complete recorded predictions, with a denominator per association."""
import argparse
import json
import random
from pathlib import Path
from analysis_io import write_json
from analyze_replication import load
import compute_validity as cv
from winner_filter import evaluate_winner, POLICY


def correlation_summary(pairs, iters=5000):
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(pairs) < 2:
        return {"spearman": None, "ci95": None, "n_valid": len(pairs), "n_bootstrap_valid": 0}
    a, b = map(list, zip(*pairs))
    point = cv.spearman(a, b)
    if point is None:
        return {"spearman": None, "ci95": None, "n_valid": len(pairs), "n_bootstrap_valid": 0}
    rnd = random.Random(42)
    values = []
    for _ in range(iters):
        chosen = [rnd.randrange(len(pairs)) for _ in pairs]
        value = cv.spearman([a[i] for i in chosen], [b[i] for i in chosen])
        if value is not None:
            values.append(value)
    values.sort()
    interval = [values[int(.025 * len(values))], values[int(.975 * len(values))]] if values else None
    return {"spearman": point, "ci95": interval, "n_valid": len(pairs), "n_bootstrap_valid": len(values)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text())
    predictions = load(args.predictions)
    rho_pairs, hit_pairs = [], []
    covered = 0
    for package in corpus:
        keys = [(package["package_id"], v["variant_id"]) for v in package["variants"]]
        if not all(k in predictions for k in keys):
            continue
        covered += 1
        real = [v["real_ctr"] for v in package["variants"]]
        pred = [predictions[k] for k in keys]
        signal = 1 - evaluate_winner(package["variants"])["adjusted_p"]
        rho_pairs.append((signal, cv.spearman(real, pred)))
        hit_pairs.append((signal, cv.top1(real, pred)))
    write_json(args.output, {"analysis_schema": cv.METRIC_POLICY, "winner_filter_policy": POLICY,
                            "signal_definition": "one_minus_simultaneous_adjusted_p",
                            "n_complete_packages": covered,
                            "signal_vs_rho": correlation_summary(rho_pairs),
                            "signal_vs_top1": correlation_summary(hit_pairs)})


if __name__ == "__main__":
    main()
