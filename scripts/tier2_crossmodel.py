#!/usr/bin/env python3
r"""Tier-2 cross-model replication: persona panel vs no-persona baseline on Upworthy CTR ranking,
using a NON-Gemini model (Azure OpenAI gpt-4.1) to test whether the headline finding
(no-persona baseline >= persona panel) holds across model families.

Faithful to the primary protocol: reuses build_prompt + parse_click_intent from run_predictions.py
(identical prompts/parsing) and the within-package metrics from compute_validity.py. Only the model
backend differs. Within-package ranking vs real CTR; package-level bootstrap CIs.

Credentials are read only from AZURE_OPENAI_* environment variables, never printed.
Checkpoints and regenerated summaries default to data/predictions/crossfamily/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1]
DATASETS = PAPER / "datasets"
PANEL = PAPER / "data" / "persona_panel.json"
OUT_DIR = PAPER / "data" / "predictions" / "crossfamily"


def _load(modname: str):
    spec = importlib.util.spec_from_file_location(modname, PAPER / "scripts" / f"{modname}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


rp = _load("run_predictions")       # build_prompt, parse_click_intent
cv = _load("compute_validity")      # kendall_tau, spearman, top1, bootstrap_ci


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", type=int, default=0, help="0=all significant-winner; else first N")
    ap.add_argument("--draws", type=int, default=3, help="persona Monte-Carlo draws")
    ap.add_argument("--baseline-draws", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--corpus", default=str(DATASETS / "upworthy-subset-2026-06-03.json"))
    ap.add_argument("--output-dir", type=Path, default=OUT_DIR,
                    help="checkpoint and summary directory (default: local, gitignored)")
    args = ap.parse_args()
    out_dir = args.output_dir

    key, url, model = load_azure()
    print("[tier2] backend=azure-openai (credentials loaded)")
    corpus = [p for p in json.loads(Path(args.corpus).read_text()) if p.get("winner_significant")]
    if args.packages > 0:
        corpus = corpus[: args.packages]
    personas = json.loads(PANEL.read_text())["personas"]
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = model.replace(".", "_").replace("/", "_").replace("\\", "_")
    ckpt = out_dir / f".ckpt-upworthy-{safe}.jsonl"

    # build all (pkg, var, who, draw) tasks; 'who' is persona id or 'baseline'
    done: dict[tuple, list[float]] = {}
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                r = json.loads(line); done.setdefault((r["pkg"], r["var"], r["who"]), []).append(r["val"])
    seen = set()
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                r = json.loads(line); seen.add((r["pkg"], r["var"], r["who"], r["draw"]))

    tasks = []
    for p in corpus:
        for v in p["variants"]:
            for persona in personas:
                for d in range(args.draws):
                    k = (p["package_id"], v["variant_id"], persona["id"], d)
                    if k not in seen:
                        tasks.append((p["package_id"], v["variant_id"], v["headline"], persona, d))
            for d in range(args.baseline_draws):
                k = (p["package_id"], v["variant_id"], "baseline", d)
                if k not in seen:
                    tasks.append((p["package_id"], v["variant_id"], v["headline"], {"id": "baseline"}, d))

    print(f"[tier2] packages={len(corpus)} personas={len(personas)} "
          f"draws={args.draws} baseline_draws={args.baseline_draws} -> {len(tasks)} calls to run")

    lock = threading.Lock(); fh = ckpt.open("a"); ok = miss = 0
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(call_azure, url, key, model, rp.build_prompt(per, h), args.temperature):
                    (pid, vid, per["id"], d) for (pid, vid, h, per, d) in tasks}
            for fut in as_completed(futs):
                pid, vid, who, d = futs[fut]; val = fut.result()
                if val is None:
                    miss += 1; continue
                ok += 1
                with lock:
                    fh.write(json.dumps({"pkg": pid, "var": vid, "who": who, "draw": d, "val": val}) + "\n"); fh.flush()
                    done.setdefault((pid, vid, who), []).append(val)
    finally:
        fh.close()
    print(f"[tier2] calls ok={ok} miss={miss}")

    # aggregate per variant: persona panel mean (all personas x draws), baseline mean (draws)
    def agg(pkg_id, var_id, who_filter):
        vals = []
        for (pk, vr, who), vs in done.items():
            if pk == pkg_id and vr == var_id and who_filter(who):
                vals += vs
        return sum(vals) / len(vals) if vals else None

    def metrics(pred_for):
        taus, rhos, hits, lifts = [], [], [], []
        n = 0
        for p in corpus:
            real = [v["real_ctr"] for v in p["variants"]]
            pred = [pred_for(p["package_id"], v["variant_id"]) for v in p["variants"]]
            if any(x is None for x in pred) or len(real) < 2:
                continue
            n += 1
            t = cv.kendall_tau(real, pred); s = cv.spearman(real, pred)
            if t is not None: taus.append(t)
            if s is not None: rhos.append(s)
            hits.append(cv.top1(real, pred))
            best, worst = max(real), min(real)
            if best > worst:
                lifts.append((real[max(range(len(pred)), key=lambda i: pred[i])] - worst) / (best - worst))
        return {"n_packages": n,
                "kendall_tau": {"mean": sum(taus)/len(taus), "ci95": cv.bootstrap_ci(taus)},
                "spearman_rho": {"mean": sum(rhos)/len(rhos), "ci95": cv.bootstrap_ci(rhos)},
                "top1_accuracy": {"mean": sum(hits)/len(hits), "ci95": cv.bootstrap_ci([float(h) for h in hits])},
                "lift_captured": {"mean": sum(lifts)/len(lifts), "ci95": cv.bootstrap_ci(lifts)}}

    panel = metrics(lambda pk, vr: agg(pk, vr, lambda w: w != "baseline"))
    base = metrics(lambda pk, vr: agg(pk, vr, lambda w: w == "baseline"))

    # PAIRED per-package gap (the correct significance test for "baseline beats persona"):
    # baseline-minus-persona on the SAME packages, then bootstrap the per-package difference.
    pe_t, ba_t, pe_h, ba_h = [], [], [], []
    for p in corpus:
        real = [v["real_ctr"] for v in p["variants"]]
        pp = [agg(p["package_id"], v["variant_id"], lambda w: w != "baseline") for v in p["variants"]]
        bp = [agg(p["package_id"], v["variant_id"], lambda w: w == "baseline") for v in p["variants"]]
        if len(real) < 2 or any(x is None for x in pp) or any(x is None for x in bp):
            continue
        pt, bt = cv.kendall_tau(real, pp), cv.kendall_tau(real, bp)
        if pt is None or bt is None:
            continue
        pe_t.append(pt); ba_t.append(bt); pe_h.append(cv.top1(real, pp)); ba_h.append(cv.top1(real, bp))
    gap_t = [b - a for a, b in zip(pe_t, ba_t)]
    gap_h = [float(b - a) for a, b in zip(pe_h, ba_h)]
    paired = {"n_paired": len(gap_t),
              "gap_tau": {"mean": sum(gap_t)/len(gap_t) if gap_t else 0.0,
                          "ci95": cv.bootstrap_ci(gap_t) if gap_t else [0, 0]},
              "gap_top1": {"mean": sum(gap_h)/len(gap_h) if gap_h else 0.0,
                           "ci95": cv.bootstrap_ci(gap_h) if gap_h else [0, 0]}}
    out = {
        "paired_gap": paired,
        "_doc": "Tier-2 cross-model replication of sim-to-real on Upworthy with a non-Gemini model.",
        "model": model, "backend": "azure-openai", "temperature": args.temperature,
        "draws": args.draws, "baseline_draws": args.baseline_draws,
        "persona_panel": panel, "no_persona_baseline": base,
        "gap_tau": base["kendall_tau"]["mean"] - panel["kendall_tau"]["mean"],
    }
    (out_dir / f"upworthy_{safe}.json").write_text(json.dumps(out, indent=2))
    print(f"\n[tier2] {model} on n={panel['n_packages']} reliable-winner packages:")
    print(f"  persona panel : tau={panel['kendall_tau']['mean']:.3f} {panel['kendall_tau']['ci95']} "
          f"top1={panel['top1_accuracy']['mean']:.3f}")
    print(f"  no-persona base: tau={base['kendall_tau']['mean']:.3f} {base['kendall_tau']['ci95']} "
          f"top1={base['top1_accuracy']['mean']:.3f}")
    pg = paired["gap_tau"]; ph = paired["gap_top1"]
    print(f"  PAIRED gap (base-persona) over n={paired['n_paired']} packages:")
    print(f"    tau  gap = {pg['mean']:+.3f} 95%CI{pg['ci95']}  "
          f"({'SIGNIFICANT' if pg['ci95'][0] > 0 else 'n.s. (CI includes 0)'})")
    print(f"    top1 gap = {ph['mean']:+.3f} 95%CI{ph['ci95']}  "
          f"({'SIGNIFICANT' if ph['ci95'][0] > 0 else 'n.s. (CI includes 0)'})")
    print(f"  wrote {out_dir / f'upworthy_{safe}.json'}")


if __name__ == "__main__":
    main()
