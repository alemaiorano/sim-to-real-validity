#!/usr/bin/env python3
"""Offline reanalysis of explicitly identified historical GPT post-parser scores.

No provider or credential loading. This cannot establish original-response validity.
"""
import argparse
import hashlib
import json
from pathlib import Path
from analysis_io import write_json
from tier2_crossmodel import checkpoint_analysis
from winner_filter import evaluate_winner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--expected-corpus-sha256", required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus_bytes, checkpoint_bytes = args.corpus.read_bytes(), args.checkpoint.read_bytes()
    corpus_hash = hashlib.sha256(corpus_bytes).hexdigest()
    checkpoint_hash = hashlib.sha256(checkpoint_bytes).hexdigest()
    if corpus_hash != args.expected_corpus_sha256 or checkpoint_hash != args.expected_checkpoint_sha256:
        raise ValueError("input source hash mismatch")
    corpus = json.loads(corpus_bytes)
    rows = [json.loads(line) for line in checkpoint_bytes.splitlines() if line.strip()]
    for row in rows:
        if type(row["draw"]) is not int or not 0 <= row["draw"] < (10 if row["who"] == "baseline" else 3):
            raise ValueError("observation outside recorded historical draw budget")
    report = checkpoint_analysis(corpus, rows, legacy_scores=True)
    legacy = {p["package_id"] for p in corpus if p.get("winner_significant")}
    eligible = {p["package_id"] for p in corpus if evaluate_winner(p["variants"])["selected"]}
    if not eligible <= legacy:
        raise ValueError("corrected packages are not a subset of the historical population")
    report.update(provider_calls=0, provenance={"corpus_sha256": corpus_hash,
                  "checkpoint_sha256": checkpoint_hash, "n_observations": len(rows),
                  "legacy_report_commit": "7c1ab46b5d881529b79769fb870ed1f2fb98619c",
                  "legacy_eligible_packages": len(legacy), "corrected_eligible_packages": len(eligible), "corrected_ids_subset_of_legacy": True},
                  scope="retrospective diagnostic on recorded post-parser values; not an independent replication")
    write_json(args.output, report)


if __name__ == "__main__":
    main()
