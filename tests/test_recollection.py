"""Paid-call prevention, durable raw retention and independent replay contracts."""
import base64
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recollect as rc
from analyze_recollection import replay


def response(score=.7):
    return json.dumps({"candidates": [{"finishReason": "STOP", "content": {
        "parts": [{"text": json.dumps({"click_intent": score})}]}}],
        "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 10, "totalTokenCount": 30},
        "modelVersion": "fixture-version", "responseId": "fixture-id"}).encode()


class RecollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name) / "run"
        self.backup = Path(self.temp.name) / "backup"
        for directory in [self.run, self.backup]:
            (directory / "inputs").mkdir(parents=True)
        self.panel = json.loads((ROOT / "data/persona_panel.json").read_text())["personas"]
        self.corpus = [{"package_id": "p", "variants": [
            {"variant_id": "a", "headline": "First headline", "real_ctr": .1, "clicks": 100, "impressions": 1000},
            {"variant_id": "b", "headline": "Second headline", "real_ctr": .3, "clicks": 300, "impressions": 1000}]}]
        self.tasks = rc.make_tasks(self.corpus, self.panel)
        self.plan = {"protocol": rc.PROTOCOL, "task_plan_sha256": rc.digest(rc.encoded(self.tasks)),
                     "backup_directory": str(self.backup), "code_sha256": {},
                     "input_sha256": {"corpus.json": rc.digest(rc.encoded(self.corpus))},
                     "selected_package_ids": ["p"], "primary_coverage": "complete",
                     "temperature": .8, "max_output_tokens": 64,
                     "workers": 1, "initial_requests_per_second": 100000,
                     "max_attempts_per_observation": 3, "max_total_attempts_per_model": 1000,
                     "backends": {backend: {"model": "fixture", "cap_usd": "1",
                     "requests_per_minute": 1000000000,
                     "accounting_input_per_million": ".50", "accounting_output_per_million": "3"}
                     for backend in ["gemini", "azure"]}}
        self.write_plan()

    def write_plan(self):
        requests = {b: rc.make_requests(self.tasks, b) for b in self.plan["backends"]}
        self.plan["request_plan_sha256"] = {b: rc.digest(rc.encoded(rows)) for b, rows in requests.items()}
        for directory in [self.run, self.backup]:
            (directory / "plan.json").write_bytes(rc.encoded(self.plan) + b"\n")
            (directory / "tasks.json").write_bytes(rc.encoded(self.tasks) + b"\n")
            (directory / "inputs/corpus.json").write_bytes(rc.encoded(self.corpus))
            for backend, rows in requests.items():
                (directory / f"requests-{backend}.json").write_bytes(rc.encoded(rows) + b"\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_real_allocation_is_balanced_and_interleaved(self):
        self.assertEqual(len(self.tasks), 120)
        self.assertEqual(len({t["task_id"] for t in self.tasks}), 120)
        for first, second in zip(self.tasks[::2], self.tasks[1::2]):
            self.assertEqual(first["variant_id"], second["variant_id"])
            self.assertEqual(first["pair"], second["pair"])
            self.assertEqual(first["seed"], second["seed"])
            self.assertEqual(sum(t["persona_id"] == "baseline" for t in [first, second]), 1)
        counts = Counter((t["variant_id"], t["persona_id"]) for t in self.tasks)
        self.assertEqual(counts[("a", "baseline")], 30)
        self.assertTrue(all(n == 3 for (var, who), n in counts.items() if who != "baseline"))

    def test_raw_response_is_saved_twice_and_replayed_without_provider(self):
        raw = response()
        calls = []
        def transport(body):
            calls.append(body)
            return 200, raw, {"request-id": "retained", "Authorization": "must-not-save"}
        collection = rc.Collection(self.run, "gemini", {}, transport)
        result = collection.execute()
        self.assertTrue(result["complete"])
        self.assertEqual(len(calls), 120)
        self.assertEqual((self.run / "gemini.events.jsonl").read_bytes(), (self.backup / "gemini.events.jsonl").read_bytes())
        rows = [json.loads(line) for line in (self.run / "gemini.events.jsonl").read_text().splitlines()]
        saved = next(r for r in rows if r["event"] == "result")
        self.assertEqual(base64.b64decode(saved["response_body_base64"]), raw)
        self.assertNotIn("authorization", saved["response_headers"])
        report = replay(self.run, "gemini")
        self.assertEqual(report["n_primary_packages"], 1)
        self.assertEqual(report["primary"]["paired_gap"]["metrics"]["top1_accuracy"]["n_paired"], 1)
        resumed = rc.Collection(self.run, "gemini", {}, lambda _: self.fail("completed observations repeated"))
        self.assertTrue(resumed.execute()["complete"])

    def test_budget_prevents_dispatch(self):
        self.plan["backends"]["gemini"]["cap_usd"] = "0"
        self.write_plan()
        collection = rc.Collection(self.run, "gemini", {}, lambda _: self.fail("unbudgeted provider call"))
        result = collection.execute()
        self.assertTrue(result["stopped"])
        self.assertEqual(result["attempts"], 0)

    def test_terminal_invalid_content_is_not_retried_or_replaced(self):
        calls = []
        def invalid(body):
            calls.append(body)
            return 200, response(True), {}
        collection = rc.Collection(self.run, "gemini", {}, invalid)
        collection.execute(limit=2)
        self.assertEqual(len(calls), 2)
        report = replay(self.run, "gemini")
        self.assertEqual(report["n_primary_packages"], 0)
        self.assertEqual(report["attempt_status_counts"], {"invalid_content": 2})

    def test_unknown_interrupted_attempt_retains_liability_and_is_not_reissued(self):
        collection = rc.Collection(self.run, "gemini", {}, lambda _: self.fail("unexpected transport"))
        task = collection.tasks[0]
        collection.journal.append({"event": "dispatch", "task_id": task["task_id"],
            "attempt_id": task["task_id"] + ":0", "reserved_usd": ".1",
            "observation": {k: v for k, v in task.items() if k != "prompt"},
            "request": rc.request_body(self.plan, "gemini", task)})
        collection.journal.close()
        resumed = rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {}))
        self.assertIn(task["task_id"], resumed.done)
        self.assertEqual(resumed.spent, Decimal(".1"))
        resumed.execute(limit=0)
        self.assertEqual(replay(self.run, "gemini")["interrupted_attempts"], 1)

    def test_transient_attempt_resume_uses_next_attempt_identity(self):
        collection = rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {}))
        task = self.tasks[0]
        attempt_id = task["task_id"] + ":0"
        collection.journal.append({"event": "dispatch", "task_id": task["task_id"],
                                  "attempt_id": attempt_id, "reserved_usd": ".001"})
        collection.journal.append({"event": "result", "task_id": task["task_id"],
                                  "attempt_id": attempt_id, "accounted_usd": None, "terminal": False})
        collection.journal.close()
        resumed = rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {}))
        resumed.execute(limit=1)
        dispatches = [r["attempt_id"] for r in resumed.journal.rows() if r["event"] == "dispatch"]
        self.assertEqual(dispatches, [attempt_id, task["task_id"] + ":1"])

    def test_mirror_failure_preserves_primary_raw_event(self):
        journal = rc.Journal(self.run, self.backup, "failure")
        actual = journal.streams[1]
        class Broken:
            def write(self, _): raise OSError("fixture unavailable backup")
        journal.streams[1] = Broken()
        with self.assertRaises(OSError):
            journal.append({"event": "fixture", "raw": "must survive"})
        self.assertEqual(next(journal.rows())["raw"], "must survive")
        journal.streams[1] = actual
        journal.close()

    def test_chain_or_plan_tampering_fails_closed(self):
        collection = rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {}))
        collection.execute(limit=1)
        self.plan["temperature"] = .1
        self.write_plan()
        with self.assertRaises(ValueError):
            rc.Collection(self.run, "gemini", {}, lambda _: self.fail("changed-plan provider call"))

    def test_valid_json_with_truncated_finish_is_invalid(self):
        body = json.loads(response())
        body["candidates"][0]["finishReason"] = "MAX_TOKENS"
        self.assertIsNone(rc.interpret("gemini", json.dumps(body).encode())["score"])

    def test_azure_three_choices_keep_balanced_observations_and_usage_once(self):
        calls = []
        raw = json.dumps({"choices": [
            {"index": i, "finish_reason": "stop", "message": {"content": '{"click_intent":0.7}'}}
            for i in range(3)], "usage": {"prompt_tokens": 20, "completion_tokens": 30},
            "model": "fixture-gpt", "id": "fixture-response"}).encode()
        def transport(body):
            calls.append(body)
            self.assertEqual(body["n"], 3)
            return 200, raw, {}
        collection = rc.Collection(self.run, "azure", {}, transport)
        self.assertEqual(len(collection.tasks), 40)
        for first, second in zip(collection.tasks[::2], collection.tasks[1::2]):
            self.assertEqual(first["variant_id"], second["variant_id"])
            self.assertEqual(sum(t["persona_id"] == "baseline" for t in [first, second]), 1)
        collection.execute()
        self.assertEqual(len(calls), 40)
        report = replay(self.run, "azure")
        self.assertEqual(report["terminal_observations"], 120)
        self.assertEqual(report["token_counts"], [800, 1200])
        self.assertEqual(report["n_primary_packages"], 1)

    def test_missing_or_duplicate_choice_indices_are_terminal_invalid(self):
        for indices in [[0, 1], [0, 0, 2], [0, 1, 4]]:
            raw = json.dumps({"choices": [{"index": i, "finish_reason": "stop",
                "message": {"content": '{"click_intent":0.8}'}} for i in indices]}).encode()
            result = rc.interpret("azure", raw, 3)
            self.assertEqual(result["scores"], [None, None, None])
            self.assertFalse(result["choice_indices_valid"])

    def test_quota_headers_and_retry_after_ms_control_future_dispatch(self):
        collection = rc.Collection(self.run, "azure", {}, lambda _: self.fail("no call expected"))
        import time
        start = time.monotonic()
        collection.limit_headers({"x-ratelimit-limit-requests": "150",
                                  "x-ratelimit-limit-tokens": "150000",
                                  "retry-after-ms": "6000"}, 429, 800)
        self.assertGreaterEqual(collection.interval, 60 / (.9 * 150))
        self.assertGreaterEqual(collection.next_dispatch, start + 6)
        collection.journal.close()

    def test_azure_reserves_all_three_choice_outputs_before_dispatch(self):
        request = rc.make_requests(self.tasks, "azure")[0]
        counts = [len(request["prompt"].encode()) + 256, self.plan["max_output_tokens"]]
        self.plan["backends"]["azure"]["cap_usd"] = str(rc.cost(counts, self.plan["backends"]["azure"]))
        self.write_plan()
        collection = rc.Collection(self.run, "azure", {}, lambda _: self.fail("three choices exceeded reservation"))
        self.assertTrue(collection.execute(limit=1)["stopped"])

    def test_permanent_failure_stays_halted_after_resume(self):
        first = rc.Collection(self.run, "gemini", {}, lambda _: (400, b'{"error":"fixture"}', {}))
        self.assertTrue(first.execute(limit=1)["stopped"])
        resumed = rc.Collection(self.run, "gemini", {}, lambda _: self.fail("persisted stop was bypassed"))
        self.assertTrue(resumed.execute(limit=1)["stopped"])

    def test_underestimated_reservation_stays_halted_after_resume(self):
        body = json.loads(response())
        body["usageMetadata"]["totalTokenCount"] = 5000
        first = rc.Collection(self.run, "gemini", {}, lambda _: (200, json.dumps(body).encode(), {}))
        self.assertTrue(first.execute(limit=1)["stopped"])
        resumed = rc.Collection(self.run, "gemini", {}, lambda _: self.fail("cost barrier was bypassed"))
        self.assertEqual(resumed.halt_reason, "reservation_underestimated")
        self.assertTrue(resumed.execute(limit=1)["stopped"])

    def test_replay_hash_identifies_snapshot_even_if_live_journal_grows(self):
        first = rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {}))
        first.execute(limit=1)
        before = (self.run / "gemini.events.jsonl").read_bytes()
        import compute_validity as cv
        analyze = cv.analyze
        invoked = []
        def grow_then_analyze(*args, **kwargs):
            if not invoked:
                invoked.append(True)
                rc.Collection(self.run, "gemini", {}, lambda _: (200, response(), {})).execute(limit=1)
            return analyze(*args, **kwargs)
        with patch.object(cv, "analyze", side_effect=grow_then_analyze):
            report = replay(self.run, "gemini")
        self.assertEqual(report["terminal_observations"], 1)
        self.assertEqual(report["journal_sha256"], rc.digest(before))
        self.assertEqual((self.run / report["journal_snapshot"]).read_bytes(), before)
        self.assertNotEqual(report["journal_sha256"], rc.digest((self.run / "gemini.events.jsonl").read_bytes()))


if __name__ == "__main__":
    unittest.main()
