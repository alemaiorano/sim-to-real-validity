"""Matched research recollection with durable raw attempts and bounded liability.

No credentials are stored. Existing historical collectors remain legacy interfaces;
this protocol is the owner of new paired, raw-retaining journal experiments.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import hashlib
import json
from pathlib import Path
import random
import subprocess
import threading
import time
import urllib.error
import urllib.request

import compute_validity as cv
from run_predictions import build_prompt, parse_click_intent
from winner_filter import evaluate_winner, POLICY

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "paired-raw-retained-v1"
CODE = ["recollect.py", "analyze_recollection.py", "run_predictions.py", "compute_validity.py", "winner_filter.py"]


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def exclusive_json(path, value):
    with Path(path).open("xb") as stream:
        stream.write(encoded(value) + b"\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())


def read_credentials(path):
    """Read only provider variables; never return unrelated environment values."""
    allowed = {"GEMINI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_BASE_URL",
               "AZURE_OPENAI_DEPLOYMENT"}
    values = {}
    for line in Path(path).read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in allowed:
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def azure_endpoint(base):
    base = base.rstrip("/")
    if not base.endswith("/openai/v1"):
        base += "/v1" if base.endswith("/openai") else "/openai/v1"
    return base + "/chat/completions"


def make_tasks(cohort, panel):
    if len(panel) != 10 or len({p["id"] for p in panel}) != 10:
        raise ValueError("the fixed study requires ten distinct personas")
    cohort = list(cohort)
    tasks = []
    rng = random.Random(20261031)
    rng.shuffle(cohort)
    for package in cohort:
        variants = list(package["variants"])
        rng.shuffle(variants)
        for variant in variants:
            for pair in range(30):
                choices = [(panel[pair % len(panel)], pair // len(panel)), ({"id": "baseline"}, pair)]
                rng.shuffle(choices)
                for person, draw in choices:
                    key = [package["package_id"], variant["variant_id"], person["id"], draw]
                    tasks.append({"task_id": digest(encoded(key)), "package_id": key[0],
                                  "variant_id": key[1], "persona_id": key[2], "draw": draw,
                                  "pair": pair, "seed": 42 + pair,
                                  "prompt": build_prompt(person, variant["headline"])})
    if len({t["task_id"] for t in tasks}) != len(tasks):
        raise ValueError("duplicate cohort observation keys")
    return tasks


def prepare(run, backup, corpus_path, csv_path, azure_base):
    """Freeze population and allocation before any model scores are inspected."""
    run, backup = Path(run).resolve(), Path(backup).resolve()
    if run == backup or run.is_relative_to(backup) or backup.is_relative_to(run):
        raise ValueError("run and backup must be separate directories")
    if run.exists() or backup.exists():
        raise FileExistsError("new run and backup directories required")
    corpus_bytes = Path(corpus_path).read_bytes()
    csv_bytes = Path(csv_path).read_bytes()
    if digest(corpus_bytes) != "523034f1fd86d4a432a57b29eb25230418dba119c3367ec04622815114cc9f85":
        raise ValueError("unexpected original exploratory corpus")
    if digest(csv_bytes) != "8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce":
        raise ValueError("unexpected original source CSV")
    panel_bytes = (ROOT / "data/persona_panel.json").read_bytes()
    panel = json.loads(panel_bytes)["personas"]
    cohort = [p for p in json.loads(corpus_bytes) if evaluate_winner(p["variants"])["selected"]]
    tasks = make_tasks(cohort, panel)
    plan = {
        "protocol": PROTOCOL, "created_utc": now(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "code_sha256": {f"scripts/{name}": digest((ROOT / "scripts" / name).read_bytes()) for name in CODE},
        "input_sha256": {"corpus.json": digest(corpus_bytes), "source.csv": digest(csv_bytes),
                         "panel.json": digest(panel_bytes)},
        "winner_filter_policy": POLICY, "n_packages": len(cohort),
        "n_variants": sum(len(p["variants"]) for p in cohort),
        "selected_package_ids": sorted(p["package_id"] for p in cohort),
        "observations_per_arm_variant": 30, "planned_observations_per_model": len(tasks),
        "task_plan_sha256": digest(encoded(tasks)), "temperature": .8, "max_output_tokens": 64,
        "max_attempts_per_observation": 3, "max_total_attempts_per_model": 45000,
        "request_timeout_seconds": 45, "workers": 24, "initial_requests_per_second": 10,
        "primary_coverage": "all_planned_observations_valid_in_both_arms_for_every_variant",
        "invalid_content_policy": "terminal; never replace with a fresh semantic draw",
        "interrupted_dispatch_policy": "terminal_unknown; reservation remains charged",
        "cost_semantics": "conservative accounting rates, not an invoice; unknown use charged at reservation",
        "backends": {
            "gemini": {"model": "gemini-3.1-flash-lite", "cap_usd": "8",
                       "accounting_input_per_million": "0.50", "accounting_output_per_million": "3.00",
                       "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
                       "thinking": "MINIMAL"},
            "azure": {"model": "gpt-4.1", "cap_usd": "32",
                      "accounting_input_per_million": "4.00", "accounting_output_per_million": "16.00",
                      "endpoint": azure_endpoint(azure_base), "thinking": None}},
        "backup_directory": str(backup),
        "scope": "new observations on a historically selected population; not recovery of historical generations",
    }
    run.mkdir(parents=True)
    backup.mkdir(parents=True)
    for directory in [run, backup]:
        (directory / "inputs").mkdir()
        for name, content in [("corpus.json", corpus_bytes), ("source.csv", csv_bytes), ("panel.json", panel_bytes)]:
            (directory / "inputs" / name).write_bytes(content)
        exclusive_json(directory / "plan.json", plan)
        exclusive_json(directory / "tasks.json", tasks)
    return plan


class Journal:
    """One append owner serializes attempts to two durable, hash-chained copies."""
    def __init__(self, run, backup, backend):
        self.path = Path(run) / f"{backend}.events.jsonl"
        self.mirror = Path(backup) / self.path.name
        if self.path.exists() != self.mirror.exists():
            raise ValueError("missing journal mirror; preserve and reconcile before resuming")
        if self.path.exists() and digest(self.path.read_bytes()) != digest(self.mirror.read_bytes()):
            raise ValueError("journal copies differ")
        self.previous = "0" * 64
        self.sequence = 0
        self.lock = threading.Lock()
        for row in self.rows():
            body = {k: v for k, v in row.items() if k != "sha256"}
            if row["previous"] != self.previous or row["sequence"] != self.sequence or digest(encoded(body)) != row["sha256"]:
                raise ValueError("invalid journal chain")
            self.previous = row["sha256"]
            self.sequence += 1
        self.streams = [p.open("ab", buffering=0) for p in [self.path, self.mirror]]

    def rows(self):
        if self.path.exists():
            with self.path.open() as stream:
                for line in stream:
                    yield json.loads(line)

    def append(self, event):
        import os
        with self.lock:
            row = {**event, "utc": now(), "sequence": self.sequence, "previous": self.previous}
            row["sha256"] = digest(encoded(row))
            content = encoded(row) + b"\n"
            errors = []
            for stream in self.streams:
                try:
                    if stream.write(content) != len(content):
                        raise OSError("short journal write")
                    os.fsync(stream.fileno())
                except OSError as error:
                    errors.append(error)
            self.previous = row["sha256"]
            self.sequence += 1
            if errors:
                raise errors[0]
        return row

    def close(self):
        for stream in self.streams:
            stream.close()


def request_body(plan, backend, task):
    if backend == "gemini":
        return {"contents": [{"role": "user", "parts": [{"text": task["prompt"]}]}],
                "generationConfig": {"temperature": plan["temperature"], "seed": task["seed"],
                                     "maxOutputTokens": plan["max_output_tokens"],
                                     "responseMimeType": "application/json",
                                     "thinkingConfig": {"thinkingLevel": "MINIMAL"}}}
    return {"model": plan["backends"][backend]["model"],
            "messages": [{"role": "user", "content": task["prompt"]}],
            "temperature": plan["temperature"], "seed": task["seed"],
            "max_tokens": plan["max_output_tokens"], "response_format": {"type": "json_object"}}


def interpret(backend, raw):
    """Derive scores and accounting from the retained response, not stored summaries."""
    try:
        data = json.loads(raw)
        if backend == "gemini":
            candidate = data.get("candidates", [{}])[0]
            parts = candidate.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            finished = candidate.get("finishReason") == "STOP"
            usage = data.get("usageMetadata", {})
            inp, total = usage.get("promptTokenCount"), usage.get("totalTokenCount")
            out = total - inp if type(inp) is int and type(total) is int else None
            version, response_id = data.get("modelVersion"), data.get("responseId")
        else:
            choice = data.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content") or ""
            finished = choice.get("finish_reason") == "stop"
            usage = data.get("usage", {})
            inp, out = usage.get("prompt_tokens"), usage.get("completion_tokens")
            version, response_id = data.get("model"), data.get("id")
        score = parse_click_intent(text) if finished else None
        token_counts = [inp, out] if all(type(x) is int and x >= 0 for x in [inp, out]) else None
        return {"score": score, "status": "valid" if score is not None else "invalid_content",
                "text": text, "token_counts": token_counts, "model_version": version,
                "response_id": response_id}
    except (ValueError, TypeError, IndexError, AttributeError):
        return {"score": None, "status": "invalid_content", "text": None,
                "token_counts": None, "model_version": None, "response_id": None}


def cost(counts, settings):
    return (Decimal(counts[0]) * Decimal(settings["accounting_input_per_million"]) +
            Decimal(counts[1]) * Decimal(settings["accounting_output_per_million"])) / Decimal(1000000)


class Collection:
    def __init__(self, run, backend, credentials, transport=None):
        self.run = Path(run)
        self.plan = json.loads((self.run / "plan.json").read_text())
        self.tasks = json.loads((self.run / "tasks.json").read_text())
        self.backend = backend
        self.settings = self.plan["backends"][backend]
        self.backup = Path(self.plan["backup_directory"])
        self.transport = transport or self.http
        self.credentials = credentials
        if transport is None:
            required = ["GEMINI_API_KEY"] if backend == "gemini" else [
                "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_BASE_URL", "AZURE_OPENAI_DEPLOYMENT"]
            if any(not credentials.get(key) for key in required):
                raise ValueError("missing provider configuration")
            if backend == "azure" and (
                azure_endpoint(credentials["AZURE_OPENAI_BASE_URL"]) != self.settings["endpoint"] or
                credentials["AZURE_OPENAI_DEPLOYMENT"] != self.settings["model"]
            ):
                raise ValueError("Azure configuration differs from the plan")
        for name in ["plan.json", "tasks.json"]:
            if (self.run / name).read_bytes() != (self.backup / name).read_bytes():
                raise ValueError("changed configuration mirror")
        if digest(encoded(self.tasks)) != self.plan["task_plan_sha256"]:
            raise ValueError("changed task plan")
        for name, expected in self.plan["code_sha256"].items():
            if digest((ROOT / name).read_bytes()) != expected:
                raise ValueError("changed collector dependency: " + name)
        for name, expected in self.plan["input_sha256"].items():
            if digest((self.run / "inputs" / name).read_bytes()) != expected:
                raise ValueError("changed input: " + name)
        self.journal = Journal(self.run, self.backup, backend)
        self.lock = threading.Lock()
        self.spent = Decimal(0)
        self.pending = {}
        self.done = set()
        self.attempts = 0
        self.next_attempt = {}
        self.stop = threading.Event()
        self.next_dispatch = 0.
        self.interval = 1 / self.plan["initial_requests_per_second"]
        self.plan_sha256 = digest((self.run / "plan.json").read_bytes())
        for row in self.journal.rows():
            if row["event"] == "manifest":
                if row["plan_sha256"] != self.plan_sha256 or row["backend"] != backend:
                    raise ValueError("journal belongs to a different plan")
            elif row["event"] == "dispatch":
                self.pending[row["attempt_id"]] = Decimal(row["reserved_usd"])
                self.attempts += 1
                self.next_attempt[row["task_id"]] = int(row["attempt_id"].rsplit(":", 1)[1]) + 1
            elif row["event"] == "result":
                reserved = self.pending.pop(row["attempt_id"])
                self.spent += Decimal(row["accounted_usd"]) if row["accounted_usd"] is not None else reserved
                if row["terminal"]:
                    self.done.add(row["task_id"])
        # An interrupted dispatch may already have been billed: do not repeat it silently.
        for row in list(self.journal.rows()):
            if row["event"] == "dispatch" and row["attempt_id"] in self.pending:
                self.done.add(row["task_id"])
        self.spent += sum(self.pending.values(), Decimal(0))
        self.pending = {}
        if self.journal.sequence == 0:
            self.journal.append({"event": "manifest", "plan_sha256": self.plan_sha256, "backend": backend})

    def record(self, event):
        try:
            return self.journal.append(event)
        except Exception:
            self.stop.set()
            raise

    def http(self, body):
        if self.backend == "gemini":
            headers = {"x-goog-api-key": self.credentials["GEMINI_API_KEY"]}
        else:
            if azure_endpoint(self.credentials["AZURE_OPENAI_BASE_URL"]) != self.settings["endpoint"]:
                raise ValueError("Azure endpoint differs from the frozen plan")
            if self.credentials["AZURE_OPENAI_DEPLOYMENT"] != self.settings["model"]:
                raise ValueError("Azure deployment differs from the frozen plan")
            headers = {"Authorization": "Bearer " + self.credentials["AZURE_OPENAI_API_KEY"]}
        headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.settings["endpoint"], data=encoded(body), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.plan["request_timeout_seconds"]) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, error.read(), dict(error.headers)

    def observe(self, task):
        body = request_body(self.plan, self.backend, task)
        reservation = cost([len(task["prompt"].encode()) + 256, self.plan["max_output_tokens"]], self.settings)
        for attempt in range(self.next_attempt.get(task["task_id"], 0), self.plan["max_attempts_per_observation"]):
            if self.stop.is_set():
                return
            with self.lock:
                if self.attempts >= self.plan["max_total_attempts_per_model"] or self.spent + sum(self.pending.values(), Decimal(0)) + reservation > Decimal(self.settings["cap_usd"]):
                    self.stop.set()
                    return
                attempt_id = f"{task['task_id']}:{attempt}"
                self.pending[attempt_id] = reservation
                self.attempts += 1
                pause = max(0., self.next_dispatch - time.monotonic())
                self.next_dispatch = max(time.monotonic(), self.next_dispatch) + self.interval
            time.sleep(pause)
            if self.stop.is_set():
                with self.lock:
                    self.pending.pop(attempt_id)
                return
            self.record({"event": "dispatch", "attempt_id": attempt_id,
                                 "task_id": task["task_id"], "observation": {k: v for k, v in task.items() if k != "prompt"},
                                 "request": body, "reserved_usd": str(reservation)})
            started = time.monotonic()
            try:
                status, raw, headers = self.transport(body)
                error_type = None
            except (OSError, TimeoutError) as error:
                status, raw, headers, error_type = None, b"", {}, type(error).__name__
            for key in ["GEMINI_API_KEY", "AZURE_OPENAI_API_KEY"]:
                secret = self.credentials.get(key)
                if secret:
                    raw = raw.replace(secret.encode(), b"[REDACTED]")
            parsed = interpret(self.backend, raw) if status == 200 else {
                "score": None, "status": "transport_error" if status is None else "http_error",
                "token_counts": None, "text": None, "model_version": None, "response_id": None}
            retry = (status is None or status in [429, 500, 502, 503, 504]) and attempt + 1 < self.plan["max_attempts_per_observation"]
            charge = cost(parsed["token_counts"], self.settings) if parsed["token_counts"] else None
            allowed_headers = {k.lower(): v for k, v in headers.items()
                               if k.lower() in {"request-id", "x-request-id", "apim-request-id",
                                                "retry-after", "x-ms-region", "x-ratelimit-remaining-requests",
                                                "x-ratelimit-limit-requests"}}
            self.record({"event": "result", "attempt_id": attempt_id, "task_id": task["task_id"],
                                 "terminal": not retry, "http_status": status, "error_type": error_type,
                                 "response_body_base64": base64.b64encode(raw).decode(),
                                 "response_sha256": digest(raw), "response_headers": allowed_headers,
                                 "seconds": time.monotonic() - started, "parsed": parsed,
                                 "accounted_usd": str(charge) if charge is not None else None})
            with self.lock:
                self.pending.pop(attempt_id)
                self.spent += charge if charge is not None else reservation
                if not retry:
                    self.done.add(task["task_id"])
                if status in [400, 401, 403, 404] or (charge is not None and charge > reservation):
                    self.stop.set()
                if status == 429:
                    self.interval = min(2., self.interval * 2)
                    self.next_dispatch = max(self.next_dispatch, time.monotonic() + 5)
            if not retry:
                return
            time.sleep(min(30, 2 ** (attempt + 1)))

    def execute(self, limit=None):
        tasks = [t for t in self.tasks if t["task_id"] not in self.done]
        if limit is not None:
            tasks = tasks[:limit]
        with ThreadPoolExecutor(max_workers=self.plan["workers"]) as executor:
            # Bound the dispatched queue; a stop cannot leave thousands of paid tasks pending.
            width = self.plan["workers"]
            for offset in range(0, len(tasks), width):
                if self.stop.is_set():
                    break
                futures = [executor.submit(self.observe, task) for task in tasks[offset:offset + width]]
                for future in as_completed(futures):
                    future.result()
                if offset % (width * 10) == 0:
                    print(json.dumps({"backend": self.backend, "terminal_observations": len(self.done),
                                      "planned": len(self.tasks), "attempts": self.attempts,
                                      "accounted_usd": str(self.spent)}), flush=True)
        result = {"backend": self.backend, "terminal_observations": len(self.done),
                  "planned": len(self.tasks), "attempts": self.attempts, "accounted_usd": str(self.spent),
                  "complete": len(self.done) == len(self.tasks), "stopped": self.stop.is_set(),
                  "journal_sha256": digest(self.journal.path.read_bytes())}
        self.journal.close()
        return result


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--backup-dir", type=Path, required=True)
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--source-csv", type=Path, required=True)
    p.add_argument("--azure-base-url", required=True)
    c = commands.add_parser("collect")
    c.add_argument("--run-dir", type=Path, required=True)
    c.add_argument("--backend", choices=["gemini", "azure"], required=True)
    c.add_argument("--env-file", type=Path, required=True)
    c.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "collect" and args.limit is not None and args.limit < 0:
        parser.error("--limit must be nonnegative")
    if args.command == "prepare":
        print(json.dumps(prepare(args.run_dir, args.backup_dir, args.corpus, args.source_csv, args.azure_base_url), indent=2))
    else:
        lock_file = (args.run_dir / f".{args.backend}.lock").open("a")
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        collector = Collection(args.run_dir, args.backend, read_credentials(args.env_file))
        print(json.dumps(collector.execute(args.limit)), flush=True)


if __name__ == "__main__":
    main()
