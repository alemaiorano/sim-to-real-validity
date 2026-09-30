#!/usr/bin/env python3
"""Validate the per-variant predictions produced by run_predictions.py.

The primary file contains mean click-intent over the persona panel and draws.
Select another model/split with --predictions. This validator makes no LLM calls.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
PREDICTIONS = PAPER_DIR / "data" / "predictions" / "gemini-3_1-flash-lite-sig3.jsonl"

# pred_score is mean click-intent in [0,1], matching the benchmark outcome.
REQUIRED_FIELDS = {
    "package_id": str,
    "variant_id": str,
    "pred_score": (int, float),   # PRIMARY: mean click-intent in [0,1], used for ranking
}


def fail(msg: str) -> None:
    print(f"[personas][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def validate(predictions: Path = PREDICTIONS) -> None:
    if not predictions.exists():
        fail(
            f"predictions artifact missing: {predictions}\n"
            f"  Produce it by running scripts/run_predictions.py over the locked corpus\n"
            f"  (one JSONL line per package variant). This is a hard blocker."
        )
    n = 0
    seen_packages: set[str] = set()
    with predictions.open() as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                fail(f"line {i}: invalid JSON ({e})")
            for field, typ in REQUIRED_FIELDS.items():
                if field not in rec:
                    fail(f"line {i}: missing required field '{field}'")
                if not isinstance(rec[field], typ):
                    fail(f"line {i}: field '{field}' has wrong type")
                if field == "pred_score" and not (0.0 <= float(rec[field]) <= 1.0):
                    fail(f"line {i}: pred_score {rec[field]} out of [0,1]")
            seen_packages.add(rec["package_id"])
            n += 1
    print(f"[personas] OK: {n} prediction records across {len(seen_packages)} packages")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-only", action="store_true",
                    help="validate the selected per-variant predictions against the contract")
    ap.add_argument("--predictions", type=Path, default=PREDICTIONS,
                    help="prediction JSONL (default: primary persona panel)")
    args = ap.parse_args()
    if args.validate_only:
        validate(args.predictions)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
