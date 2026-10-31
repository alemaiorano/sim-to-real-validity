#!/usr/bin/env python3
"""Join complete predictions to counts-derived winner policy in a new CSV."""
import argparse
import csv
import json
import math
from pathlib import Path
from analysis_io import new_output
from winner_filter import evaluate_winner, POLICY

PAPER_DIR = Path(__file__).resolve().parents[1]
OUT = PAPER_DIR / "data/joined-corrected.csv"


def load_predictions(path):
    predictions = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["package_id"], row["variant_id"])
        if key in predictions:
            raise ValueError("duplicate prediction: " + str(key))
        value = row["pred_score"]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("invalid predicted score")
        predictions[key] = value
    return predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    destination = new_output(args.output)
    corpus = json.loads(args.corpus.read_text())
    predictions = load_predictions(args.predictions)
    rows = []
    for package in corpus:
        keys = [(package["package_id"], v["variant_id"]) for v in package["variants"]]
        covered = [key in predictions for key in keys]
        if not any(covered):
            continue
        if not all(covered):
            raise ValueError("partially predicted package: " + package["package_id"])
        decision = evaluate_winner(package["variants"])
        for variant in package["variants"]:
            rows.append({"package_id": package["package_id"], "variant_id": variant["variant_id"],
                         "real_ctr": variant["real_ctr"],
                         "pred_score": predictions[(package["package_id"], variant["variant_id"])],
                         "winner_selected": int(decision["selected"]),
                         "winner_adjusted_p": decision["adjusted_p"], "winner_filter_policy": POLICY})
    if not rows:
        raise ValueError("no joined rows produced")
    with destination.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {destination}: {len(rows)} variants")


if __name__ == "__main__":
    main()
