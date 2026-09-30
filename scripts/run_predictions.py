#!/usr/bin/env python3
"""Run the persona panel over Upworthy headline variants to produce click-intent predictions.

For each (model, package, variant, persona, draw) it asks the model, conditioned on the
persona, for a click-intent in [0,1]. pred_score per variant = mean click-intent over the
panel (and draws). Output: one JSONL per model under data/predictions/<model>.jsonl, in the
schema validated by 02_run_personas.py.

This study harness calls the Gemini API directly. GEMINI_API_KEY is read from the
environment or a local .env; its value is never printed. Pilot vs full run is
controlled by --packages.

Usage:
  python scripts/run_predictions.py --models gemini-3.1-flash-lite,gemini-2.5-flash,gemini-3.5-flash \
      --packages 12 --draws 1 --concurrency 8
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
PANEL = PAPER_DIR / "data" / "persona_panel.json"
OUT_DIR = PAPER_DIR / "data" / "predictions"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def fail(msg: str) -> None:
    print(f"[run][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        for env in (PAPER_DIR / ".env",):
            if env.exists():
                for line in env.read_text().splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("\r")
                        break
            if key:
                break
    if not key:
        fail("GEMINI_API_KEY not found in environment or local .env")
    return key


def latest_corpus(corpus_path: str | None = None) -> list[dict]:
    if corpus_path:
        p = Path(corpus_path)
        if not p.exists():
            fail(f"corpus not found: {p}")
        return json.loads(p.read_text())
    cands = [c for c in sorted(DATASETS.glob("upworthy-subset-*.json"))
             if not c.name.endswith(".manifest.json")]
    if not cands:
        fail(f"no corpus in {DATASETS}; run 01_ingest_upworthy.py")
    return json.loads(cands[-1].read_text())


JSON_TAIL = "Respond ONLY with JSON: {\"click_intent\": <number between 0 and 1>}."


def build_prompt(persona: dict, headline: str, variant: str = "default") -> str:
    if persona.get("id") == "baseline":
        if variant == "appeal":  # reworded baseline (prompt-robustness ablation)
            return (f"Estimate, for a general U.S. social-media news audience in 2014, the "
                    f"click-through appeal of this headline.\n\nHeadline: \"{headline}\"\n\n{JSON_TAIL}")
        # default no-persona zero-shot baseline: generic reader, no demographic conditioning.
        return (f"You are a typical U.S. social-media news reader in 2014.\n\n"
                f"Headline: \"{headline}\"\n\nHow likely are you to click this headline? {JSON_TAIL}")
    desc = (f"{persona['description']} (age {persona['age_group']}, {persona['gender']}, mainly on "
            f"{persona['platform']}, news engagement: {persona['news_engagement']}.)")
    if variant == "third_person":  # third-person framing (tests if first-person role-play drives it)
        return (f"Consider this person: {desc}\n\nHeadline: \"{headline}\"\n\n"
                f"How likely is this person to click this headline? {JSON_TAIL}")
    # default first-person persona role-play.
    return (f"You are simulating a specific person reacting to a news headline on social media in 2014.\n"
            f"Person: {desc}\n\nHeadline: \"{headline}\"\n\n"
            f"As this exact person, how likely are you to click this headline? {JSON_TAIL}")


_FLOAT = re.compile(r"-?\d*\.?\d+")


def parse_click_intent(text: str) -> float | None:
    try:
        obj = json.loads(text)
        v = float(obj["click_intent"])
        return v if 0.0 <= v <= 1.0 else max(0.0, min(1.0, v))
    except Exception:
        m = _FLOAT.search(text or "")
        if m:
            v = float(m.group())
            return max(0.0, min(1.0, v))
    return None


def call_model(key: str, model: str, prompt: str, temperature: float, seed: int,
               retries: int = 3, timeout: int = 60) -> float | None:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "seed": seed,                       # reproducibility (Gemini honours seed)
            "responseMimeType": "application/json",
            # Disable thinking: the task is a single scalar judgment, not multi-step reasoning.
            # flash-lite performs no thinking by default; this makes the config explicit, fair
            # across model tiers, and ~7x cheaper on thinking-enabled tiers.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode()
    url = API.format(model=model)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "x-goog-api-key": key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                d = json.loads(resp.read())
            text = d["candidates"][0]["content"]["parts"][0]["text"]
            return parse_click_intent(text)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(1 + attempt)
                continue
            return None
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="comma-separated model ids")
    ap.add_argument("--packages", type=int, default=12, help="number of packages (pilot subset)")
    ap.add_argument("--draws", type=int, default=1, help="Monte Carlo draws per persona")
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=42, help="base LLM seed; draw d uses seed+d")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--out-suffix", default="", help="suffix for output filenames (e.g. -pilot)")
    ap.add_argument("--significant-only", action="store_true",
                    help="restrict to packages with a statistically significant ground-truth winner")
    ap.add_argument("--baseline", action="store_true",
                    help="no-persona zero-shot baseline (single generic reader); use with --draws N")
    ap.add_argument("--corpus", default=None, help="explicit corpus JSON path (else latest upworthy-subset)")
    ap.add_argument("--variant", default="default",
                    choices=["default", "third_person", "appeal"],
                    help="prompt-robustness ablation variant")
    args = ap.parse_args()

    key = load_api_key()
    if args.baseline:
        panel = [{"id": "baseline"}]   # single generic reader; --draws controls samples/variant
    else:
        panel = json.loads(PANEL.read_text())["personas"]
    corpus = latest_corpus(args.corpus)
    if args.significant_only:
        corpus = [p for p in corpus if p.get("winner_significant")]
    if args.packages > 0:               # 0 = all packages; otherwise take the first N
        corpus = corpus[: args.packages]
    if not corpus:
        fail("no packages selected (check --packages / --significant-only)")
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_calls = sum(len(p["variants"]) for p in corpus) * len(panel) * args.draws
    print(f"[run] packages={len(corpus)} personas={len(panel)} draws={args.draws} "
          f"models={models} => {n_calls} calls/model")

    for model in models:
        t0 = time.time()
        safe = model.replace(".", "_")
        out = OUT_DIR / f"{safe}{args.out_suffix}.jsonl"
        # Per-observation checkpoint, appended+flushed as calls complete so a mid-run crash
        # loses nothing and the run is resumable (skip already-recorded observations).
        ckpt = OUT_DIR / f".checkpoint-{safe}{args.out_suffix}.jsonl"

        done: set[tuple[str, str, str, int]] = set()
        results: dict[tuple[str, str], list[float]] = {}
        if ckpt.exists():
            for line in ckpt.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                done.add((r["package_id"], r["variant_id"], r["persona_id"], r["draw"]))
                results.setdefault((r["package_id"], r["variant_id"]), []).append(r["value"])
            print(f"[run] {model}: resuming, {len(done)} observations already in checkpoint")

        tasks = [(pkg["package_id"], v["variant_id"], v["headline"], persona, d)
                 for pkg in corpus for v in pkg["variants"]
                 for persona in panel for d in range(args.draws)
                 if (pkg["package_id"], v["variant_id"], persona["id"], d) not in done]

        lock = threading.Lock()
        ckpt_fh = ckpt.open("a")
        ok = miss = 0
        try:
            with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
                futs = {ex.submit(call_model, key, model, build_prompt(p, h, args.variant), args.temperature, args.seed + d):
                        (pid, vid, p["id"], d) for (pid, vid, h, p, d) in tasks}
                for fut in as_completed(futs):
                    pid, vid, persona_id, d = futs[fut]
                    val = fut.result()
                    if val is None:
                        miss += 1
                        continue
                    ok += 1
                    with lock:
                        ckpt_fh.write(json.dumps({"package_id": pid, "variant_id": vid,
                                                  "persona_id": persona_id, "draw": d, "value": val}) + "\n")
                        ckpt_fh.flush()
                    results.setdefault((pid, vid), []).append(val)
        finally:
            ckpt_fh.close()

        with out.open("w") as fh:
            for pkg in corpus:
                for v in pkg["variants"]:
                    scores = results.get((pkg["package_id"], v["variant_id"]), [])
                    if not scores:
                        continue
                    fh.write(json.dumps({
                        "package_id": pkg["package_id"],
                        "variant_id": v["variant_id"],
                        "pred_score": sum(scores) / len(scores),
                        "model": model,
                        "n_obs": len(scores),
                        "n_personas": len(panel),
                        "draws": args.draws,
                        "seed": args.seed,
                        "temperature": args.temperature,
                    }) + "\n")
        total = ok + miss
        miss_pct = (miss / total * 100) if total else 0.0
        print(f"[run] {model}: ok={ok} miss={miss} ({miss_pct:.1f}% miss) "
              f"-> {out.name} in {time.time()-t0:.0f}s (checkpoint: {ckpt.name})")


if __name__ == "__main__":
    main()
