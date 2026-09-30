"""Offline regression checks for the published harness and its consumers."""
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="replication-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        (self.root / "data").mkdir()
        shutil.copyfile(ROOT / "data/persona_panel.json", self.root / "data/persona_panel.json")
        (self.root / "datasets").mkdir()
        self.corpus = self.root / "datasets/upworthy-subset-2026-06-03.json"
        self.corpus.write_text(json.dumps([
            {"package_id": "synthetic-package", "winner_significant": True,
             "variants": [
                 {"variant_id": "a", "headline": "Headline A", "real_ctr": 0.1},
                 {"variant_id": "b", "headline": "Headline B", "real_ctr": 0.2},
             ]}
        ]))

    def load(self, script):
        spec = importlib.util.spec_from_file_location(script, self.root / "scripts" / script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_cli(self, script, *args):
        return subprocess.run([sys.executable, str(self.root / "scripts" / script), *args],
                              cwd=self.root, capture_output=True, text=True)

    def produce(self, baseline=False):
        runner = self.load("run_predictions.py")
        args = ["run_predictions.py", "--models", "gemini-3.1-flash-lite", "--packages", "0",
                "--draws", "3", "--out-suffix=" + ("-baseline" if baseline else "-sig3")]
        if baseline:
            args.append("--baseline")
        with mock.patch.object(sys, "argv", args), \
                mock.patch.object(runner, "load_api_key", return_value="synthetic-key"), \
                mock.patch.object(runner, "call_model",
                                  side_effect=lambda key, model, prompt, *rest:
                                  0.8 if '"Headline B"' in prompt else 0.2), \
                contextlib.redirect_stdout(io.StringIO()):
            runner.main()
        return runner.OUT_DIR / ("gemini-3_1-flash-lite-baseline.jsonl" if baseline
                                 else "gemini-3_1-flash-lite-sig3.jsonl")

    def test_real_producer_reaches_default_validator_and_join(self):
        predictions = self.produce()
        validate = self.run_cli("02_run_personas.py", "--validate-only")
        self.assertEqual(validate.returncode, 0, validate.stderr)
        joined = self.run_cli("03_build_joined.py")
        self.assertEqual(joined.returncode, 0, joined.stderr)
        expected = {r["variant_id"]: r["pred_score"]
                    for r in map(json.loads, predictions.read_text().splitlines())}
        with (self.root / "data/joined.csv").open() as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["variant_id"]: float(r["pred_score"]) for r in rows}, expected)
        self.assertEqual({r["variant_id"]: float(r["real_ctr"]) for r in rows}, {"a": 0.1, "b": 0.2})

    def test_explicit_prediction_selection_uses_the_real_baseline_output(self):
        predictions = self.produce(baseline=True)
        validate = self.run_cli("02_run_personas.py", "--validate-only", "--predictions", str(predictions))
        self.assertEqual(validate.returncode, 0, validate.stderr)
        joined = self.run_cli("03_build_joined.py", "--predictions", str(predictions),
                              "--corpus", str(self.corpus))
        self.assertEqual(joined.returncode, 0, joined.stderr)

    def test_partial_package_cannot_be_joined(self):
        predictions = self.produce()
        predictions.write_text(predictions.read_text().splitlines()[0] + "\n")
        joined = self.run_cli("03_build_joined.py")
        self.assertNotEqual(joined.returncode, 0)
        self.assertIn("partially predicted", joined.stderr)
        self.assertFalse((self.root / "data/joined.csv").exists())

    def test_out_of_range_prediction_is_rejected(self):
        predictions = self.produce()
        rows = list(map(json.loads, predictions.read_text().splitlines()))
        rows[0]["pred_score"] = 1.1
        predictions.write_text("\n".join(map(json.dumps, rows)) + "\n")
        validate = self.run_cli("02_run_personas.py", "--validate-only")
        self.assertNotEqual(validate.returncode, 0)
        self.assertIn("out of [0,1]", validate.stderr)

    def test_azure_uses_environment_credentials_only(self):
        runner = self.load("tier2_crossmodel.py")
        (self.root / ".env").write_text("AZURE_OPENAI_API_KEY=synthetic-local-key\n")
        with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runner.load_azure()
        with mock.patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "synthetic-env-key",
                                         "AZURE_OPENAI_BASE_URL": "https://example.invalid/openai/v1",
                                         "AZURE_OPENAI_DEPLOYMENT": "gpt-4.1"}, clear=True):
            key, url, model = runner.load_azure()
        self.assertEqual(key, "synthetic-env-key")
        self.assertEqual(url, "https://example.invalid/openai/v1/chat/completions")
        self.assertEqual(model, "gpt-4.1")

    def test_azure_runner_writes_local_checkpoint_and_paired_summary(self):
        runner = self.load("tier2_crossmodel.py")
        published = self.root / "reports/crossfamily_gpt41.json"
        published.parent.mkdir()
        published.write_text("published-artifact-sentinel")
        output = io.StringIO()

        def response(url, key, model, prompt, temperature):
            baseline = "typical U.S." in prompt
            winner = '"Headline B"' in prompt
            return 0.9 if baseline == winner else 0.1

        with mock.patch.object(sys, "argv", ["tier2_crossmodel.py"]), \
                mock.patch.object(runner, "load_azure", return_value=(
                    "synthetic-private-key", "https://example.invalid/chat/completions", "gpt-4.1")), \
                mock.patch.object(runner, "call_azure", side_effect=response), \
                contextlib.redirect_stdout(output):
            runner.main()
        report = json.loads((runner.OUT_DIR / "upworthy_gpt-4_1.json").read_text())
        self.assertEqual(report["paired_gap"]["n_paired"], 1)
        self.assertEqual(report["paired_gap"]["gap_tau"]["mean"], 2.0)
        self.assertEqual(report["paired_gap"]["gap_top1"]["mean"], 1.0)
        self.assertTrue((runner.OUT_DIR / ".ckpt-upworthy-gpt-4_1.jsonl").exists())
        self.assertEqual(published.read_text(), "published-artifact-sentinel")
        self.assertNotIn("synthetic-private-key", output.getvalue())
        self.assertNotIn("example.invalid", output.getvalue())


if __name__ == "__main__":
    unittest.main()
