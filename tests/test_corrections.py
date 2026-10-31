"""Behavioral contracts for the correction, independent of the archived scores."""
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_io
import compute_validity as cv
import historical_results as historical
import run_predictions as runner
import tier2_crossmodel as tier2
import winner_filter as winner
import analyze_h5_aggregation as h5


class MetricsTests(unittest.TestCase):
    def test_gamma_and_tau_b_are_distinct_with_partial_ties(self):
        self.assertEqual(cv.goodman_kruskal_gamma([1, 2, 3], [1, 1, 2]), 1)
        self.assertAlmostEqual(cv.kendall_tau_b([1, 2, 3], [1, 1, 2]), math.sqrt(2 / 3))
        self.assertFalse(hasattr(cv, "kendall_tau"))

    def test_tau_b_matches_scipy_on_adversarial_ties(self):
        try:
            from scipy.stats import kendalltau
        except ImportError:
            self.skipTest("SciPy is an optional test oracle, not a runtime dependency")
        rng = random.Random(817)
        for _ in range(120):
            a = [rng.randrange(4) for _ in range(8)]
            b = [rng.randrange(4) for _ in range(8)]
            expected = float(kendalltau(a, b).statistic)
            actual = cv.kendall_tau_b(a, b)
            if math.isnan(expected):
                self.assertIsNone(actual)
            else:
                self.assertAlmostEqual(actual, expected, places=12)

    def test_extreme_credit_is_permutation_invariant(self):
        real, pred = [1., 2., 3.], [.9, .9, .1]
        expected = cv.metric_values(real, pred)
        for order in itertools.permutations(range(3)):
            self.assertEqual(cv.metric_values([real[i] for i in order], [pred[i] for i in order]), expected)
        self.assertEqual(cv.top1([1, 2, 3], [1, 1, 1]), 1 / 3)
        self.assertEqual(cv.top1([2, 2, 1], [1, 1, 1]), 2 / 3)
        self.assertEqual(cv.lift_captured([1, 2, 3], [1, 1, 1]), .5)

    def test_undefined_is_not_zero_and_metric_denominators_are_independent(self):
        panel = {"tied": [(1, .5), (2, .5)], "ordered": [(1, .1), (2, .8)]}
        base = {"tied": [(1, .1), (2, .8)], "ordered": [(1, .1), (2, .8)]}
        report = cv.analyze(panel, iters=50)
        self.assertEqual(report["goodman_kruskal_gamma"]["n_valid"], 1)
        self.assertEqual(report["top1_accuracy"]["n_valid"], 2)
        gaps = cv.paired_analysis(panel, base, iters=50)["metrics"]
        self.assertEqual(gaps["kendall_tau_b"]["n_paired"], 1)
        self.assertEqual(gaps["top1_accuracy"]["n_paired"], 2)
        self.assertIsNone(cv.lift_captured([1, 1], [.1, .9]))
        empty = cv.analyze({}, iters=50)
        self.assertIsNone(empty["kendall_tau_b"]["mean"])
        self.assertIsNone(empty["kendall_tau_b"]["ci95"])

    def test_random_reference_counts_observed_tied_maxima(self):
        report = cv.analyze({"p": [(2, .1), (2, .9), (1, .3)]}, iters=50)
        self.assertEqual(report["random_top1_baseline"], 2 / 3)

    def test_pair_signs_do_not_underflow(self):
        self.assertEqual(cv.goodman_kruskal_gamma([0, 1e-200], [0, 1e-200]), 1)
        self.assertEqual(cv.kendall_tau_b([0, 1e-200], [0, 1e-200]), 1)

    def test_invalid_vectors_fail(self):
        for real, pred in [([1], [1]), ([1, 2], [1]), ([1, 2], [1, float("nan")]), ([1, 2], [True, 1])]:
            with self.assertRaises(ValueError):
                cv.metric_values(real, pred)


class FilterTests(unittest.TestCase):
    @staticmethod
    def row(clicks, impressions):
        return {"clicks": clicks, "impressions": impressions, "real_ctr": clicks / impressions}

    def test_direction_selection_is_bilateral_and_all_competitors_must_pass(self):
        tied = [self.row(100, 1000), self.row(100, 1000)]
        self.assertFalse(winner.evaluate_winner(tied)["selected"])
        strong = [self.row(1000, 10000), self.row(800, 10000)]
        self.assertTrue(winner.evaluate_winner(strong)["selected"])
        self.assertFalse(winner.evaluate_winner(strong + [self.row(0, 1)])["selected"])

    def test_bonferroni_uses_all_pairs_and_is_order_invariant(self):
        rows = [self.row(3000, 10000), self.row(1000, 10000), self.row(500, 10000)]
        expected = winner.evaluate_winner(rows)
        self.assertEqual(expected["n_pairs"], 3)
        for ordered in itertools.permutations(rows):
            result = winner.evaluate_winner(ordered)
            self.assertEqual(result["selected"], expected["selected"])
            self.assertEqual(result["adjusted_p"], expected["adjusted_p"])

    def test_null_two_arm_screen_has_approximately_nominal_rate(self):
        import numpy as np
        rng = np.random.default_rng(20261031)
        draws = rng.binomial(10000, .05, size=(10000, 2))
        accepted = sum(winner.evaluate_winner([self.row(int(a), 10000), self.row(int(b), 10000)])["selected"] for a, b in draws)
        self.assertLess(accepted / len(draws), .065)
        self.assertGreater(accepted / len(draws), .035)

    def test_counts_and_stored_ctr_must_agree(self):
        with self.assertRaises(ValueError):
            winner.evaluate_winner([{"clicks": 100, "impressions": 1000, "real_ctr": .9}, self.row(80, 1000)])


class ParserAndAggregationTests(unittest.TestCase):
    def test_strict_score_parser(self):
        self.assertEqual(runner.parse_click_intent('{"click_intent":0.7}'), .7)
        for text in ['{"click_intent":true}', '{"click_intent":7}', '{"click_intent":NaN}',
                     '{"click_intent":"0.7"}', '{"click_intent":0.1,"click_intent":0.9}', 'I am 68 years old.', '0.7', '{"click_intent":null}']:
            self.assertIsNone(runner.parse_click_intent(text), text)

    def test_invalid_content_is_terminal_under_the_documented_policy(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"candidates": [{"content": {"parts": [{"text": "No score"}]}}]}).encode()
        with patch.object(runner.urllib.request, "urlopen", return_value=Response()) as call:
            self.assertIsNone(runner.call_model("stub", "stub", "stub", .8, 42))
            self.assertEqual(call.call_count, 1)

    def test_observation_weight_and_persona_weight_do_not_silently_merge(self):
        raw = {"pkg": {"A": {"p1": [.9, .9, .9], "p2": [.1]}, "B": {"p1": [.6] * 3, "p2": [.6] * 3}}}
        collapsed = h5.collapse_personas(raw)["pkg"]
        observed = h5.mean_observation(raw["pkg"])
        weighted = h5.agg_level(collapsed, "mean")
        self.assertGreater(observed["A"], observed["B"])
        self.assertLess(weighted["A"], weighted["B"])
        self.assertEqual(h5.agg_borda({"a": {"p1": .2}, "b": {"p2": .4}}), {})

    def test_legacy_checkpoint_is_not_a_current_collection(self):
        corpus = [{"package_id": "p", "variants": [{"variant_id": "a", "real_ctr": .1, "clicks": 100, "impressions": 1000},
                                                   {"variant_id": "b", "real_ctr": .3, "clicks": 300, "impressions": 1000}]}]
        rows = [{"pkg": "p", "var": "a", "who": "p01", "draw": 0, "val": .5}]
        with self.assertRaises(ValueError):
            tier2.checkpoint_packages(corpus, rows, config_sha256="new-config")
        tier2.checkpoint_packages(corpus, rows, legacy_scores=True)


class ArtifactTests(unittest.TestCase):
    def test_pinned_historical_artifacts_and_adapter(self):
        manifest = json.loads((ROOT / "reports/legacy-provenance.json").read_text())
        for name, expected in manifest["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / "reports" / name).read_bytes()).hexdigest(), expected)
        result = historical.read_historical("correlation.json")
        self.assertIn("goodman_kruskal_gamma", result)
        self.assertNotIn("kendall_tau", result)
        with self.assertRaises(ValueError):
            historical.read_historical("modern-statistics.json")

    def test_analysis_output_never_overwrites_history_or_an_existing_file(self):
        with self.assertRaises(ValueError):
            analysis_io.write_json(ROOT / "reports/correlation.json", {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            analysis_io.write_json(path, {"result": 1})
            with self.assertRaises(FileExistsError):
                analysis_io.write_json(path, {"result": 2})
            self.assertEqual(json.loads(path.read_text()), {"result": 1})


if __name__ == "__main__":
    unittest.main()
