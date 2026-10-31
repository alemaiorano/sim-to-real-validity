#!/usr/bin/env python3
"""Analyze explicitly supplied pilot predictions under the corrected policy."""
import argparse
import json
from pathlib import Path
from analysis_io import write_json
from analyze_replication import load, metrics
from winner_filter import POLICY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text())
    write_json(args.output, {"winner_filter_policy": POLICY, "models": {
        str(path): metrics(corpus, load(path)) for path in args.predictions}})


if __name__ == "__main__":
    main()
