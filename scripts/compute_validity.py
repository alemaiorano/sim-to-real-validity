#!/usr/bin/env python3
"""Ranking estimators and paired summaries for corrected analyses.
Historical JSONs are not rewritten. Gamma and Kendall tau-b have distinct keys;
decision metrics use expected uniform tie credit, never first-position credit.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from pathlib import Path
from analysis_io import write_json
from winner_filter import POLICY

PAPER_DIR = Path(__file__).resolve().parents[1]
JOINED = PAPER_DIR / "data" / "joined-corrected.csv"
BOOTSTRAP_ITERS = 10000
SEED = 42
METRIC_POLICY = "ranking-validity-v2-uniform-ties"
METRICS = ("goodman_kruskal_gamma", "kendall_tau_b", "spearman_rho",
           "top1_accuracy", "bottom1_accuracy", "lift_captured")


def _validate(a, b):
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("ranking requires equal vectors with at least two observations")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in [*a, *b]):
        raise ValueError("ranking inputs must be finite numbers")


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a, b):
    _validate(a, b)
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def _pairs(a, b):
    _validate(a, b)
    c = d = ties_a = ties_b = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            da = (a[i] > a[j]) - (a[i] < a[j])
            db = (b[i] > b[j]) - (b[i] < b[j])
            if da == 0:
                ties_a += 1
            if db == 0:
                ties_b += 1
            product = da * db
            c += product > 0
            d += product < 0
    return c, d, ties_a, ties_b


def goodman_kruskal_gamma(a, b):
    c, d, _, _ = _pairs(a, b)
    return (c - d) / (c + d) if c + d else None


def kendall_tau_b(a, b):
    c, d, ta, tb = _pairs(a, b)
    pairs = len(a) * (len(a) - 1) // 2
    den = math.sqrt((pairs - ta) * (pairs - tb))
    return (c - d) / den if den else None


def _extreme_credit(real, pred, operation):
    _validate(real, pred)
    choices = [i for i, value in enumerate(pred) if value == operation(pred)]
    target = operation(real)
    return sum(real[i] == target for i in choices) / len(choices)


def top1(real, pred):
    return _extreme_credit(real, pred, max)


def bottom1(real, pred):
    return _extreme_credit(real, pred, min)


def lift_captured(real, pred):
    _validate(real, pred)
    best, worst = max(real), min(real)
    if best == worst:
        return None
    selected = [r for r, p in zip(real, pred) if p == max(pred)]
    return (sum(selected) / len(selected) - worst) / (best - worst)


def metric_values(real, pred):
    return {
        "goodman_kruskal_gamma": goodman_kruskal_gamma(real, pred),
        "kendall_tau_b": kendall_tau_b(real, pred),
        "spearman_rho": spearman(real, pred),
        "top1_accuracy": top1(real, pred),
        "bottom1_accuracy": bottom1(real, pred),
        "lift_captured": lift_captured(real, pred),
    }


def bootstrap_ci(values, iters=BOOTSTRAP_ITERS):
    if not values:
        return None
    if type(iters) is not int or iters < 2:
        raise ValueError("at least two bootstrap resamples required")
    rnd = random.Random(SEED)
    means = sorted(sum(values[rnd.randrange(len(values))] for _ in values) / len(values) for _ in range(iters))
    return [means[int(.025 * iters)], means[min(int(.975 * iters), iters - 1)]]


def summarize(values, iters=BOOTSTRAP_ITERS):
    values = list(values)
    valid = [v for v in values if v is not None]
    if any(not math.isfinite(v) for v in valid):
        raise ValueError("non-finite metric")
    return {"mean": sum(valid) / len(valid) if valid else None,
            "ci95": bootstrap_ci(valid, iters), "n_total": len(values),
            "n_valid": len(valid), "n_undefined": len(values) - len(valid)}


def analyze(pkgs, iters=BOOTSTRAP_ITERS):
    observations = {key: metric_values([x[0] for x in vs], [x[1] for x in vs]) for key, vs in pkgs.items()}
    result = {"metric_policy": METRIC_POLICY, "n_packages": len(pkgs),
              "n_variants": sum(len(v) for v in pkgs.values()), "package_ids": sorted(pkgs)}
    for metric in METRICS:
        result[metric] = {**summarize([v[metric] for v in observations.values()], iters),
                          "valid_package_ids": sorted(k for k, v in observations.items() if v[metric] is not None)}
    result["random_top1_baseline"] = sum(sum(x[0] == max(r[0] for r in v) for x in v) / len(v) for v in pkgs.values()) / len(pkgs) if pkgs else None
    return result


def paired_analysis(panel, baseline, iters=BOOTSTRAP_ITERS):
    shared = sorted(panel.keys() & baseline.keys())
    results = {name: [] for name in METRICS}
    valid_ids = {name: [] for name in METRICS}
    for key in shared:
        real = [x[0] for x in panel[key]]
        if real != [x[0] for x in baseline[key]]:
            raise ValueError("paired ground truth/order mismatch: " + key)
        p = metric_values(real, [x[1] for x in panel[key]])
        b = metric_values(real, [x[1] for x in baseline[key]])
        for name in METRICS:
            valid = p[name] is not None and b[name] is not None
            results[name].append(b[name] - p[name] if valid else None)
            if valid:
                valid_ids[name].append(key)
    return {"direction": "baseline_minus_panel", "metric_policy": METRIC_POLICY,
            "n_common_packages": len(shared), "metrics": {
                name: {**summarize(results[name], iters), "n_paired": len(valid_ids[name]),
                       "paired_package_ids": valid_ids[name]} for name in METRICS}}


def load_packages(path=JOINED, selected_only=False):
    result = {}
    with Path(path).open() as stream:
        for row in csv.DictReader(stream):
            if row.get("winner_filter_policy") != POLICY:
                raise ValueError("joined input must identify the corrected winner policy")
            if selected_only and row["winner_selected"] != "1":
                continue
            result.setdefault(row["package_id"], []).append((float(row["real_ctr"]), float(row["pred_score"])))
    return {k: v for k, v in result.items() if len(v) >= 2}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--joined", type=Path, default=JOINED)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected = load_packages(args.joined, selected_only=True)
    report = {"analysis_schema": METRIC_POLICY, "winner_filter_policy": POLICY,
              "selected": analyze(selected), "all_predicted": analyze(load_packages(args.joined))}
    write_json(args.output, report)


if __name__ == "__main__":
    main()
