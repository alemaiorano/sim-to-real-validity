#!/usr/bin/env python3
"""Generate paper figures from artifacts (no hand-drawn data):
  fig:comparison    — baseline vs persona panel on top-1/tau/rho with 95% CIs (the headline result)
  fig:reliability   — distribution of ground-truth winner p-values with the p<0.05 cutoff
Outputs latex/figures/*.pdf. Reads reports/baseline_comparison.json and the locked corpus.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PAPER_DIR = Path(__file__).resolve().parents[1]
DATASETS = PAPER_DIR / "datasets"
REPORTS = PAPER_DIR / "reports"
FIG = PAPER_DIR / "latex" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "figure.dpi": 150})


def fig_comparison() -> None:
    d = json.loads((REPORTS / "baseline_comparison.json").read_text())
    metrics = [("top1", "Top-1"), ("tau", "Kendall $\\tau$"), ("rho", "Spearman $\\rho$")]
    methods = [("baseline", "No-persona baseline", "#2c7fb8"), ("panel", "Persona panel", "#de2d26")]
    x = np.arange(len(metrics)); w = 0.38
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    for j, (mk, ml, col) in enumerate(methods):
        means = [d[mk][m]["mean"] for m, _ in metrics]
        lo = [d[mk][m]["mean"] - d[mk][m]["ci"][0] for m, _ in metrics]
        hi = [d[mk][m]["ci"][1] - d[mk][m]["mean"] for m, _ in metrics]
        ax.bar(x + (j - 0.5) * w, means, w, yerr=[lo, hi], capsize=3, label=ml, color=col)
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in metrics])
    ax.set_ylabel("validity (estimate, 95% CI)")
    ax.axhline(0, color="k", lw=0.6)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("No-persona baseline vs. persona panel (reliable packages)")
    fig.tight_layout(); fig.savefig(FIG / "comparison.pdf"); plt.close(fig)
    print("wrote figures/comparison.pdf")


def fig_reliability() -> None:
    candidates = [c for c in sorted(DATASETS.glob("upworthy-subset-*.json"))
                  if not c.name.endswith(".manifest.json")]
    if not candidates:
        sys.exit("[figures][FATAL] Upworthy corpus missing; restore it via DATA_SOURCES.md "
                 "or use --comparison-only to regenerate the report-backed figure")
    corpus = json.loads(candidates[-1].read_text())
    pvals = [p["winner_p_one_sided"] for p in corpus]
    sig = sum(1 for p in pvals if p < 0.05)
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.hist(pvals, bins=20, color="#7fbf7b", edgecolor="white")
    ax.axvline(0.05, color="#de2d26", ls="--", lw=1.2, label="$p=0.05$ cutoff")
    ax.set_xlabel("one-sided $p$-value of the top-vs-runner-up CTR difference")
    ax.set_ylabel("number of A/B tests")
    ax.set_title(f"Ground-truth reliability: {sig}/{len(pvals)} tests have a significant winner")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "reliability.pdf"); plt.close(fig)
    print("wrote figures/reliability.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparison-only", action="store_true",
                    help="regenerate comparison.pdf from reports without the raw corpus")
    args = ap.parse_args()
    if not args.comparison_only:
        fig_reliability()
    fig_comparison()
