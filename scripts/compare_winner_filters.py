"""Compare the recorded legacy selection with the corrected screen, without predictions."""
import argparse
import hashlib
import json
from pathlib import Path
from analysis_io import write_json
from winner_filter import evaluate_winner

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    content = args.corpus.read_bytes()
    corpus = json.loads(content)
    old = {p["package_id"] for p in corpus if p["winner_significant"]}
    new = {p["package_id"] for p in corpus if evaluate_winner(p["variants"])["selected"]}
    write_json(args.output, {
        "corpus_sha256": hashlib.sha256(content).hexdigest(), "n_eligible": len(corpus),
        "legacy_selected": len(old), "corrected_selected": len(new),
        "corrected_ids_subset_of_legacy": new <= old, "legacy_only": len(old-new),
        "corrected_only": len(new-old), "corrected_package_ids": sorted(new),
        "scope": "screen comparison only; removed packages are not demonstrated false winners"})

if __name__ == "__main__":
    main()
