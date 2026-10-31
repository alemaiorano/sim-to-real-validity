"""Replay the pinned historical producer offline, with missing draws remaining missing."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from analysis_io import write_json
from tier2_crossmodel import checkpoint_packages

PIN = "7c1ab46b5d881529b79769fb870ed1f2fb98619c"
ROOT = Path(__file__).resolve().parents[1]
FILES = ["scripts/tier2_crossmodel.py", "scripts/run_predictions.py",
         "scripts/compute_validity.py", "data/persona_panel.json", "reports/crossfamily_gpt41.json"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--expected-corpus-sha256", required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus_bytes, checkpoint_bytes = args.corpus.read_bytes(), args.checkpoint.read_bytes()
    ch, kh = hashlib.sha256(corpus_bytes).hexdigest(), hashlib.sha256(checkpoint_bytes).hexdigest()
    if (ch, kh) != (args.expected_corpus_sha256, args.expected_checkpoint_sha256):
        raise ValueError("historical input hash mismatch")
    corpus = json.loads(corpus_bytes)
    rows = [json.loads(line) for line in checkpoint_bytes.splitlines() if line.strip()]
    checkpoint_packages(corpus, rows, legacy_scores=True)  # validates identity, duplicates and score domain
    legacy_ids = {p["package_id"] for p in corpus if p["winner_significant"]}
    for row in rows:
        if row["pkg"] not in legacy_ids or not 0 <= row["draw"] < (10 if row["who"] == "baseline" else 3):
            raise ValueError("row outside the historical selected draw population")
    producer_hashes = {}
    with tempfile.TemporaryDirectory() as directory:
        tree = Path(directory)
        for name in FILES:
            content = subprocess.check_output(["git", "show", PIN + ":" + name], cwd=ROOT)
            producer_hashes[name] = hashlib.sha256(content).hexdigest()
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        output = tree / "output"
        output.mkdir()
        shutil.copyfile(args.checkpoint, output / ".ckpt-upworthy-gpt-4_1.jsonl")
        spec = importlib.util.spec_from_file_location("historical_gpt", tree / "scripts/tier2_crossmodel.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        argv = ["historical_gpt", "--corpus", str(args.corpus.resolve()), "--output-dir", str(output)]
        with patch.object(sys, "argv", argv), patch.object(runner, "load_azure", return_value=("offline", "https://example.invalid", "gpt-4.1")), patch.object(runner, "call_azure", return_value=None) as missing, patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), contextlib.redirect_stdout(io.StringIO()):
            runner.main()
        expected = json.loads((tree / "reports/crossfamily_gpt41.json").read_text())
        actual = json.loads((output / "upworthy_gpt-4_1.json").read_text())
        differences = []
        def compare(a, b, path=""):
            if isinstance(a, dict):
                if not isinstance(b, dict) or set(a) != set(b):
                    differences.append(path + ": keys")
                else:
                    for key in a:
                        compare(a[key], b[key], path + "/" + key)
            elif isinstance(a, list):
                if not isinstance(b, list) or len(a) != len(b):
                    differences.append(path + ": length")
                else:
                    for i, (x, y) in enumerate(zip(a,b)):
                        compare(x, y, path + "/" + str(i))
            elif type(a) in (int, float) and type(b) in (int, float):
                if not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
                    differences.append(path)
            elif a != b:
                differences.append(path)
        compare(expected, actual)
        report = {"source_commit": PIN, "producer_file_sha256": producer_hashes,
                  "corpus_sha256": ch, "checkpoint_sha256": kh, "observations": len(rows),
                  "legacy_packages": len(legacy_ids), "provider_calls": 0,
                  "missing_observation_stubs": missing.call_count, "differences": differences,
                  "numeric_tolerance": {"absolute": 1e-12, "relative": 1e-12},
                  "legacy_reproduced": not differences, "original_responses_available": False}
    write_json(args.output, report)
    if differences:
        raise ValueError("historical replay mismatch; see output differences")

if __name__ == "__main__":
    main()
