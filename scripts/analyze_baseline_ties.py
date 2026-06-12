#!/usr/bin/env python3
"""Quantify the no-persona baseline's within-package tie behaviour on the primary (exploratory)
significant packages, for the transparency/robustness note: the baseline is less granular than the
panel, so a minority of packages tie; ties are broken arbitrarily with negligible effect, and they
drag the baseline down (making the reported gap a conservative lower bound).

Outputs reports/baseline_ties.json. Reproducible (reads the locked corpus + baseline predictions).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
spec = importlib.util.spec_from_file_location("cv", PAPER_DIR / "scripts" / "compute_validity.py")
cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)


def main() -> None:
    corpus = json.loads((DATASETS / "upworthy-subset-2026-06-03.json").read_text())
    sig = {p["package_id"] for p in corpus if p.get("winner_significant")}
    preds = {}
    for line in (PAPER_DIR / "data" / "predictions" / "gemini-3_1-flash-lite-baseline.jsonl").open():
        r = json.loads(line); preds[(r["package_id"], r["variant_id"])] = float(r["pred_score"])

    n = degen = top1_cur = 0
    top1_fair = 0.0
    nd_hits = nd_n = 0
    for p in corpus:
        if p["package_id"] not in sig:
            continue
        keys = [(p["package_id"], v["variant_id"]) for v in p["variants"]]
        if len(keys) < 2 or not all(k in preds for k in keys):
            continue
        real = [v["real_ctr"] for v in p["variants"]]
        pr = [preds[k] for k in keys]
        n += 1
        is_degen = len(set(round(x, 6) for x in pr)) == 1
        if is_degen:
            degen += 1
            top1_fair += 1.0 / len(pr)            # expected credit under random tie-break
        else:
            h = cv.top1(real, pr)
            top1_fair += h
            nd_hits += h; nd_n += 1
        top1_cur += cv.top1(real, pr)

    out = {
        "dataset": "upworthy-exploratory (primary, significant-winner)",
        "n_packages": n,
        "tie_rate": round(degen / n, 4),
        "top1_arbitrary_tiebreak": round(top1_cur / n, 4),
        "top1_fair_tiebreak": round(top1_fair / n, 4),
        "top1_non_degenerate": round(nd_hits / nd_n, 4),
    }
    (PAPER_DIR / "reports" / "baseline_ties.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
