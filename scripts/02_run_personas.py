#!/usr/bin/env python3
"""Contract + validator for the persona-prediction artifact.

The persona simulation runs in the product API (TypeScript,
`apps/api/src/services/simulation-runner.ts`), not here. This script does NOT
call the LLM. It (a) documents the exact schema the API must emit, and
(b) validates a produced `data/sim_predictions.jsonl` against that schema so the
downstream join can trust it. Missing predictions are a BLOCKER, not an action item.

How to produce the predictions (to be wired as an API/CLI batch job):
  For each package variant in the locked corpus, run the simulator with personas
  derived from the Upworthy audience (NOT internal product personas), one record
  per (package_id, variant_id), capturing the raw `intentProxy` + `microSurvey`
  fields plus a single scalar `pred_score` used for ranking.

Each JSONL line MUST match REQUIRED_FIELDS below. `pred_score` is the scalar the
ranking metrics consume; document its definition in latex/sections/05-setup.tex.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
PREDICTIONS = PAPER_DIR / "data" / "sim_predictions.jsonl"

# Design decision (locked 2026-06-03): the PRIMARY pred_score is a dedicated click-intent
# elicitation (mean over personas of "would you click this headline?", 0-1), because it
# matches the Upworthy CTR construct. The product's UNMODIFIED intentProxy is also captured
# as a SECONDARY signal: comparing how well click-intent vs purchaseLikelihood predict real
# CTR is precisely the RQ2 construct-gap measurement. Both must be present per record.
REQUIRED_FIELDS = {
    "package_id": str,
    "variant_id": str,
    "pred_score": (int, float),   # PRIMARY: mean click-intent in [0,1], used for ranking
}
# SECONDARY (product intact) — enables the RQ2 construct-gap comparison.
REQUIRED_INTENT = {"trialLikelihood", "demoLikelihood", "purchaseLikelihood"}


def fail(msg: str) -> None:
    print(f"[personas][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def validate() -> None:
    if not PREDICTIONS.exists():
        fail(
            f"predictions artifact missing: {PREDICTIONS}\n"
            f"  Produce it by running the product simulator over the locked corpus\n"
            f"  (one JSONL line per package variant). This is a hard blocker."
        )
    n = 0
    seen_packages: set[str] = set()
    with PREDICTIONS.open() as fh:
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
            # intentProxy is the SECONDARY (RQ2 construct-gap) signal; optional during the
            # pilot. If present it must be well-formed.
            intent = rec.get("intentProxy")
            if intent is not None and not REQUIRED_INTENT.issubset(intent):
                fail(f"line {i}: intentProxy present but missing {sorted(REQUIRED_INTENT)}")
            seen_packages.add(rec["package_id"])
            n += 1
    print(f"[personas] OK: {n} prediction records across {len(seen_packages)} packages")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-only", action="store_true",
                    help="validate data/sim_predictions.jsonl against the contract")
    args = ap.parse_args()
    if args.validate_only:
        validate()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
