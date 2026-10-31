"""Recompute the paired experiment entirely from saved provider response bytes."""
import argparse
import base64
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

from analysis_io import write_json
import compute_validity as cv
from recollect import digest, encoded, interpret, request_body, cost, PROTOCOL


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
    lookup = {t["task_id"]: t for t in tasks}
    dispatches, outcomes, responded = {}, {}, set()
    previous = "0" * 64
    statuses, versions = Counter(), Counter()
    tokens = [0, 0]
    accounted = Decimal(0)
    rows = 0
    with (run / f"{backend}.events.jsonl").open() as stream:
        for sequence, line in enumerate(stream):
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
                parsed = interpret(backend, raw) if row["http_status"] == 200 else None
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
                    if row["task_id"] in outcomes:
                        raise ValueError("multiple terminal outcomes for one observation")
                    outcomes[row["task_id"]] = parsed["score"] if parsed else None
                    versions[str(parsed["model_version"]) if parsed else "unknown"] += 1
            else:
                raise ValueError("unknown journal event")
    interrupted = set(dispatches) - responded
    for key in interrupted:
        task_id = dispatches[key]["task_id"]
        accounted += Decimal(dispatches[key]["reserved_usd"])
        outcomes.setdefault(task_id, None)
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
    return {"protocol": PROTOCOL, "backend": backend, "model_requested": plan["backends"][backend]["model"],
            "plan_sha256": digest((run / "plan.json").read_bytes()),
            "journal_sha256": digest((run / f"{backend}.events.jsonl").read_bytes()),
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
