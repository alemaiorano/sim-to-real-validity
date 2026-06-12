#!/usr/bin/env python3
"""H003 (doesitstand science #1): does the simulator's predictive validity rise with the
ground-truth signal strength of the A/B test? Now answerable across the FULL p-range because
predictions cover all 1695 packages (not only significant ones).

signal_strength = 1 - winner_p_one_sided ; per-package validity = per-package Spearman rho
and per-package top-1 hit. Correlate signal vs validity with bootstrap CIs. → reports/h003.json
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
    corpus = json.loads(next(c for c in sorted(DATASETS.glob("upworthy-subset-*.json"))
                             if not c.name.endswith(".manifest.json")).read_text())
    preds = {}
    for line in (PAPER_DIR / "data" / "sim_predictions.jsonl").open():
        r = json.loads(line); preds[(r["package_id"], r["variant_id"])] = float(r["pred_score"])

    signal, per_rho, per_hit = [], [], []
    for pkg in corpus:
        keys = [(pkg["package_id"], v["variant_id"]) for v in pkg["variants"]]
        if not all(k in preds for k in keys):
            continue
        real = [v["real_ctr"] for v in pkg["variants"]]
        pred = [preds[k] for k in keys]
        rho = cv.spearman(real, pred)
        if rho is None:
            continue
        signal.append(1 - pkg["winner_p_one_sided"])
        per_rho.append(rho)
        per_hit.append(float(cv.top1(real, pred)))

    # Spearman(signal, validity) + bootstrap CI on that statistic
    import random
    def boot_corr(a, b, iters=5000, seed=42):
        rnd = random.Random(seed); n = len(a); out = []
        for _ in range(iters):
            idx = [rnd.randrange(n) for _ in range(n)]
            c = cv.spearman([a[i] for i in idx], [b[i] for i in idx])
            if c is not None:
                out.append(c)
        out.sort()
        return [out[int(0.025*len(out))], out[int(0.975*len(out))]]

    c_rho = cv.spearman(signal, per_rho)
    c_hit = cv.spearman(signal, per_hit)
    rep = {
        "n_packages": len(signal),
        "signal_strength_range": [min(signal), max(signal)],
        "corr_signal_vs_per_package_rho": {"spearman": c_rho, "ci95": boot_corr(signal, per_rho)},
        "corr_signal_vs_top1_hit": {"spearman": c_hit, "ci95": boot_corr(signal, per_hit)},
    }
    (PAPER_DIR / "reports" / "h003.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
