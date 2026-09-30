#!/usr/bin/env python3
"""Join the locked Upworthy corpus with persona predictions → data/joined.csv.

joined.csv is the single base artifact for every downstream statistic. One row
per (package_id, variant_id) carrying both the real CTR and the predicted score.

Fails loudly if either upstream artifact is missing or if the prediction set does
not cover the corpus (partial coverage would silently bias the ranking metrics).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = PAPER_DIR / "datasets"
PREDICTIONS = PAPER_DIR / "data" / "predictions" / "gemini-3_1-flash-lite-sig3.jsonl"
OUT = PAPER_DIR / "data" / "joined.csv"


def fail(msg: str) -> None:
    print(f"[join][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def latest_corpus() -> Path:
    candidates = sorted(DATASETS_DIR.glob("upworthy-subset-*.json"))
    candidates = [c for c in candidates if not c.name.endswith(".manifest.json")]
    if not candidates:
        fail(f"no corpus found in {DATASETS_DIR}; run 01_ingest_upworthy.py first")
    return candidates[-1]


def load_predictions(predictions: Path = PREDICTIONS) -> dict[tuple[str, str], float]:
    if not predictions.exists():
        fail(f"predictions missing: {predictions}; run run_predictions.py + 02_run_personas.py")
    preds: dict[tuple[str, str], float] = {}
    with predictions.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            preds[(rec["package_id"], rec["variant_id"])] = float(rec["pred_score"])
    return preds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", type=Path, default=PREDICTIONS,
                    help="prediction JSONL (default: primary persona panel)")
    ap.add_argument("--corpus", type=Path, help="locked corpus JSON (default: Upworthy exploratory)")
    args = ap.parse_args()
    corpus = json.loads((args.corpus or latest_corpus()).read_text())
    preds = load_predictions(args.predictions)

    rows = []
    included = skipped = 0
    for pkg in corpus:
        pid = pkg["package_id"]
        keys = [(pid, v["variant_id"]) for v in pkg["variants"]]
        have = [k in preds for k in keys]
        if not any(have):
            skipped += 1            # package was not run (e.g. non-significant subset)
            continue
        if not all(have):
            # a partially-predicted package would bias within-package ranking
            fail(f"package {pid} is partially predicted ({sum(have)}/{len(have)}); "
                 f"rerun predictions for the whole package")
        for v in pkg["variants"]:
            rows.append({
                "package_id": pid,
                "variant_id": v["variant_id"],
                "real_ctr": v["real_ctr"],
                "pred_score": preds[(pid, v["variant_id"])],
                "winner_significant": int(bool(pkg.get("winner_significant"))),
            })
        included += 1
    if not rows:
        fail("no joined rows produced")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["package_id", "variant_id", "real_ctr",
                                           "pred_score", "winner_significant"])
        w.writeheader()
        w.writerows(rows)
    print(f"[join] wrote {OUT} ({len(rows)} rows, {included} packages; {skipped} not predicted)")


if __name__ == "__main__":
    main()
