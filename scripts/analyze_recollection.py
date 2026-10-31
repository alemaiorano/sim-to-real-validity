"""Recompute the paired experiment entirely from saved provider response bytes."""
import argparse
import base64
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

from analysis_io import write_json
import compute_validity as cv
from recollect import digest, encoded, interpret, request_body, cost, PROTOCOL, validate_amendment


def replay(run, backend):
    run = Path(run)
    plan = json.loads((run / "plan.json").read_text())
    if plan["protocol"] != PROTOCOL:
        raise ValueError("unknown collection protocol")
    tasks = json.loads((run / "tasks.json").read_text())
    if digest(encoded(tasks)) != plan["task_plan_sha256"]:
        raise ValueError("changed tasks")
    for name, expected in plan["input_sha256"].items():
        if digest((run / "inputs" / name).read_bytes()) != expected:
            raise ValueError("changed input: " + name)
    requests = json.loads((run / f"requests-{backend}.json").read_text())
    if digest(encoded(requests)) != plan["request_plan_sha256"][backend]:
        raise ValueError("changed request plan")
    lookup = {t["task_id"]: t for t in requests}
    dispatches, outcomes, responded = {}, {}, set()
    previous = "0" * 64
    statuses, versions = Counter(), Counter()
    tokens = [0, 0]
    accounted = Decimal(0)
    rows = 0
    amendments = []
    journal_bytes = (run / f"{backend}.events.jsonl").read_bytes()
    if journal_bytes and not journal_bytes.endswith(b"\n"):
        raise ValueError("incomplete journal record; analyze a completed snapshot")
    snapshots = run / "snapshots"
    snapshots.mkdir(exist_ok=True)
    snapshot_path = snapshots / f"{backend}-{digest(journal_bytes)}.jsonl"
    try:
        with snapshot_path.open("xb") as stream:
            stream.write(journal_bytes)
            stream.flush()
            import os
            os.fsync(stream.fileno())
    except FileExistsError:
        if snapshot_path.read_bytes() != journal_bytes:
            raise ValueError("conflicting preserved journal snapshot")
    if journal_bytes:
        for sequence, line in enumerate(journal_bytes.splitlines()):
            row = json.loads(line)
            body = {k: v for k, v in row.items() if k != "sha256"}
            if row["sequence"] != sequence or row["previous"] != previous or digest(encoded(body)) != row["sha256"]:
                raise ValueError("broken raw journal chain")
            previous = row["sha256"]
            rows += 1
            if row["event"] == "manifest":
                if sequence != 0 or row["backend"] != backend or row["plan_sha256"] != digest((run / "plan.json").read_bytes()):
                    raise ValueError("wrong journal manifest")
            elif row["event"] == "dispatch":
                key = row["attempt_id"]
                task = lookup[row["task_id"]]
                if key in dispatches or row["request"] != request_body(plan, backend, task):
                    raise ValueError("duplicate or wrong dispatched request")
                if row["observation"] != {k: v for k, v in task.items() if k != "prompt"}:
                    raise ValueError("changed observation key")
                dispatches[key] = row
            elif row["event"] == "result":
                key = row["attempt_id"]
                if key not in dispatches or key in responded or row["task_id"] != dispatches[key]["task_id"]:
                    raise ValueError("orphan or duplicate response")
                responded.add(key)
                raw = base64.b64decode(row["response_body_base64"], validate=True)
                if digest(raw) != row["response_sha256"]:
                    raise ValueError("changed provider bytes")
                request = lookup[row["task_id"]]
                parsed = interpret(backend, raw, len(request["observations"])) if row["http_status"] == 200 else None
                if parsed is not None and parsed != row["parsed"]:
                    raise ValueError("stored parsing differs from raw response")
                counts = parsed["token_counts"] if parsed else None
                charge = cost(counts, plan["backends"][backend]) if counts else None
                if row["accounted_usd"] != (str(charge) if charge is not None else None):
                    raise ValueError("stored accounting differs from raw usage")
                accounted += charge if charge is not None else Decimal(dispatches[key]["reserved_usd"])
                if counts:
                    tokens = [a + b for a, b in zip(tokens, counts)]
                statuses[row["parsed"]["status"]] += 1
                if row["terminal"]:
                    scores = parsed["scores"] if parsed else [None] * len(request["observations"])
                    for observation, score in zip(request["observations"], scores):
                        if observation["task_id"] in outcomes:
                            raise ValueError("multiple terminal outcomes for one observation")
                        outcomes[observation["task_id"]] = score
                    versions[str(parsed["model_version"]) if parsed else "unknown"] += len(scores)
            elif row["event"] == "amendment":
                document = validate_amendment(plan, digest((run / "plan.json").read_bytes()),
                                              backend, row["amendment"], journal_bytes)
                if amendments or row["sequence"] != document["base_journal_rows"] or row["previous"] != document["base_last_event_sha256"]:
                    raise ValueError("duplicate or displaced amendment")
                amendments.append(document)
            else:
                raise ValueError("unknown journal event")
    interrupted = set(dispatches) - responded
    for key in interrupted:
        task_id = dispatches[key]["task_id"]
        accounted += Decimal(dispatches[key]["reserved_usd"])
        for observation in lookup[task_id]["observations"]:
            outcomes.setdefault(observation["task_id"], None)
    corpus = json.loads((run / "inputs/corpus.json").read_text())
    selected = {p["package_id"]: p for p in corpus if p["package_id"] in plan["selected_package_ids"]}
    values = defaultdict(list)
    planned_counts = Counter()
    for task in tasks:
        arm = "baseline" if task["persona_id"] == "baseline" else "panel"
        key = task["package_id"], task["variant_id"], arm
        planned_counts[key] += 1
        value = outcomes.get(task["task_id"])
        if value is not None:
            values[key].append(value)
    complete, available = {"panel": {}, "baseline": {}}, {"panel": {}, "baseline": {}}
    both_complete = set()
    for pid, package in selected.items():
        arm_full = {}
        for arm in ["panel", "baseline"]:
            keys = [(pid, v["variant_id"], arm) for v in package["variants"]]
            scores = [(v["real_ctr"], sum(values[k]) / len(values[k])) for v, k in zip(package["variants"], keys) if values[k]]
            if len(scores) == len(keys):
                available[arm][pid] = scores
            arm_full[arm] = all(len(values[k]) == planned_counts[k] == 30 for k in keys)
        if all(arm_full.values()):
            both_complete.add(pid)
            for arm in ["panel", "baseline"]:
                complete[arm][pid] = available[arm][pid]
    primary = {arm: cv.analyze(complete[arm]) for arm in complete}
    primary["paired_gap"] = cv.paired_analysis(complete["panel"], complete["baseline"])
    return {"protocol": PROTOCOL, "collection_amendments": amendments, "backend": backend, "model_requested": plan["backends"][backend]["model"],
            "plan_sha256": digest((run / "plan.json").read_bytes()),
            "journal_sha256": digest(journal_bytes),
            "journal_snapshot": str(snapshot_path.relative_to(run)), "journal_snapshot_bytes": len(journal_bytes),
            "n_eligible_packages": len(selected), "planned_observations": len(tasks),
            "terminal_observations": len(outcomes), "unresolved_observations": len(tasks) - len(outcomes),
            "interrupted_attempts": len(interrupted), "attempt_status_counts": dict(statuses),
            "terminal_model_version_counts": dict(versions), "token_counts": tokens,
            "accounted_usd_conservative": str(accounted), "raw_journal_rows": rows,
            "n_primary_packages": len(both_complete),
            "excluded_primary_package_ids": sorted(set(selected) - both_complete),
            "primary": primary,
            "available_observation_sensitivity": {arm: cv.analyze(available[arm]) for arm in available},
            "coverage_policy": plan["primary_coverage"],
            "scope": "new matched-budget observations; percentile intervals condition on cohort and recorded generations"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--backend", choices=["gemini", "azure"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, replay(args.run_dir, args.backend))


if __name__ == "__main__":
    main()
