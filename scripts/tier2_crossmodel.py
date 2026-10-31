#!/usr/bin/env python3
"""Collect a new strict-parser cross-family comparison, or analyze recorded scores offline.
Historical sampling used 30 panel observations versus 10 baseline draws per variant.
No generation seed is sent. New versioned checkpoints never resume historical files.
Credentials come only from AZURE_OPENAI_* environment variables.
"""
from __future__ import annotations

import argparse
import hashlib
import math
from collections import defaultdict
import importlib.util
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from analysis_io import write_json, new_output
from winner_filter import evaluate_winner, POLICY

PAPER = Path(__file__).resolve().parents[1]
DATASETS = PAPER / "datasets"
PANEL = PAPER / "data" / "persona_panel.json"
OUT_DIR = PAPER / "data" / "predictions" / "crossfamily"


def _load(modname: str):
    spec = importlib.util.spec_from_file_location(modname, PAPER / "scripts" / f"{modname}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


rp = _load("run_predictions")       # build_prompt, parse_click_intent
cv = _load("compute_validity")      # corrected metric owner


def fail(m: str) -> None:
    print(f"[tier2][FATAL] {m}", file=sys.stderr); sys.exit(1)


def load_azure() -> tuple[str, str, str]:
    """Return (api_key, URL, deployment) from environment variables only."""
    key = os.environ.get("AZURE_OPENAI_API_KEY", "")
    base = os.environ.get("AZURE_OPENAI_BASE_URL") or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    dep = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
    if not key or not base or not dep:
        fail("set AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL (or ENDPOINT), and AZURE_OPENAI_DEPLOYMENT")
    b = base.rstrip("/")
    b = b if b.endswith("/openai/v1") else (b + "/v1" if b.endswith("/openai") else b + "/openai/v1")
    return key, b + "/chat/completions", dep


def call_azure(url: str, key: str, model: str, prompt: str, temperature: float,
               retries: int = 4, timeout: int = 60) -> float | None:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature, "max_tokens": 20,
        "response_format": {"type": "json_object"},
    }).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "Authorization": "Bearer " + key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            return rp.parse_click_intent(d["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt + 1); continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(1 + attempt); continue
            return None
    return None


def checkpoint_packages(corpus, rows, *, legacy_scores=False, config_sha256=None):
    """Aggregate recorded observations once; never invoke a provider."""
    lookup = {p["package_id"]: {v["variant_id"] for v in p["variants"]} for p in corpus}
    personas = {p["id"] for p in json.loads(PANEL.read_text())["personas"]}
    values = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["pkg"], row["var"], row["who"], row["draw"])
        if key in seen:
            raise ValueError("duplicate checkpoint observation")
        seen.add(key)
        if row["pkg"] not in lookup or row["var"] not in lookup[row["pkg"]] or row["who"] not in personas | {"baseline"}:
            raise ValueError("checkpoint observation outside corpus/panel")
        if type(row["draw"]) is not int or row["draw"] < 0:
            raise ValueError("invalid checkpoint draw")
        if not legacy_scores and (row.get("collection_protocol") != rp.COLLECTION_PROTOCOL or row.get("config_sha256") != config_sha256):
            raise ValueError("checkpoint protocol/configuration mismatch")
        if not legacy_scores and (row.get("status") not in {"valid", "invalid_or_unavailable"} or
                                  (row["status"] == "invalid_or_unavailable" and row["val"] is not None)):
            raise ValueError("invalid checkpoint observation status")
        if row.get("status") == "invalid_or_unavailable" and row["val"] is None:
            continue
        val = row["val"]
        if type(val) not in (int, float) or not math.isfinite(val) or not 0 <= val <= 1:
            raise ValueError("invalid recorded score")
        arm = "baseline" if row["who"] == "baseline" else "panel"
        values[(row["pkg"], row["var"], arm)].append(val)
    selected = [p for p in corpus if evaluate_winner(p["variants"])["selected"]]
    arms = {}
    for arm in ["panel", "baseline"]:
        packages = {}
        for package in selected:
            groups = [values.get((package["package_id"], v["variant_id"], arm), []) for v in package["variants"]]
            if not all(groups):
                continue
            packages[package["package_id"]] = [(v["real_ctr"], sum(group) / len(group))
                                               for v, group in zip(package["variants"], groups)]
        arms[arm] = packages
    return arms["panel"], arms["baseline"], len(selected)


def checkpoint_analysis(corpus, rows, *, legacy_scores=False, config_sha256=None, iters=cv.BOOTSTRAP_ITERS):
    panel, baseline, eligible = checkpoint_packages(corpus, rows, legacy_scores=legacy_scores, config_sha256=config_sha256)
    return {"analysis_schema": cv.METRIC_POLICY, "winner_filter_policy": POLICY,
            "n_eligible": eligible, "n_panel_missing_coverage": eligible - len(panel),
            "n_baseline_missing_coverage": eligible - len(baseline),
            "historical_post_parser_scores": legacy_scores,
            "original_response_validity": "not_established" if legacy_scores else "strict_parser",
            "persona_panel": cv.analyze(panel, iters), "no_persona_baseline": cv.analyze(baseline, iters),
            "paired_gap": cv.paired_analysis(panel, baseline, iters)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", type=int, default=0)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--baseline-draws", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--corpus", default=str(DATASETS / "upworthy-subset-2026-06-03.json"))
    ap.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    if min(args.draws, args.baseline_draws, args.concurrency) < 1 or args.packages < 0 or not math.isfinite(args.temperature):
        ap.error("draws/concurrency must be positive; packages nonnegative; temperature finite")
    key, url, model = load_azure()
    corpus = json.loads(Path(args.corpus).read_text())
    corpus = [p for p in corpus if evaluate_winner(p["variants"])["selected"]]
    if args.packages > 0:
        corpus = corpus[:args.packages]
    if not corpus:
        fail("no packages selected")
    personas = json.loads(PANEL.read_text())["personas"]
    config = {"protocol": rp.COLLECTION_PROTOCOL, "url": url, "model": model, "corpus": corpus,
              "panel": personas, "temperature": args.temperature, "draws": args.draws,
              "baseline_draws": args.baseline_draws}
    config["prompt_sha256"] = hashlib.sha256(json.dumps(
        [rp.build_prompt(p, "{headline}") for p in [*personas, {"id": "baseline"}]], sort_keys=True).encode()).hexdigest()
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    safe = model.replace(".", "_").replace("/", "_").replace("\\", "_")
    stem = f"upworthy_{safe}-{rp.COLLECTION_PROTOCOL}-{fingerprint[:16]}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{stem}.json"
    new_output(output)
    ckpt = args.output_dir / f".ckpt-{stem}.jsonl"
    rows = [json.loads(line) for line in ckpt.read_text().splitlines() if line.strip()] if ckpt.exists() else []
    for row in rows:
        if type(row["draw"]) is not int or not 0 <= row["draw"] < (args.baseline_draws if row["who"] == "baseline" else args.draws):
            raise ValueError("checkpoint draw outside configuration")
    checkpoint_packages(corpus, rows, config_sha256=fingerprint)
    seen = {(r["pkg"], r["var"], r["who"], r["draw"]) for r in rows}
    tasks = []
    for package in corpus:
        for variant in package["variants"]:
            for persona in [*personas, {"id": "baseline"}]:
                draws = args.baseline_draws if persona["id"] == "baseline" else args.draws
                for draw in range(draws):
                    task_key = (package["package_id"], variant["variant_id"], persona["id"], draw)
                    if task_key not in seen:
                        tasks.append((task_key, rp.build_prompt(persona, variant["headline"])))
    with ckpt.open("a") as stream, ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(call_azure, url, key, model, prompt, args.temperature): task_key
                   for task_key, prompt in tasks}
        for future in as_completed(futures):
            pid, vid, who, draw = futures[future]
            val = future.result()
            row = {"pkg": pid, "var": vid, "who": who, "draw": draw, "val": val,
                   "status": "valid" if val is not None else "invalid_or_unavailable",
                   "collection_protocol": rp.COLLECTION_PROTOCOL, "config_sha256": fingerprint}
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            rows.append(row)
    report = checkpoint_analysis(corpus, rows, config_sha256=fingerprint)
    report.update(model=model, backend="azure-openai", temperature=args.temperature,
                  draws=args.draws, baseline_draws=args.baseline_draws,
                  generation_seed=None, collection_protocol=rp.COLLECTION_PROTOCOL,
                  config_sha256=fingerprint)
    write_json(output, report)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
