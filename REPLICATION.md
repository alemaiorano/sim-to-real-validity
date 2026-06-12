# Research Replication Guide

How to reproduce the empirical results, figures, macros, and statistical
artifacts in the paper **"Do Synthetic Personas Predict Real Audience Response?
A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based Copy
Simulation."**

The package supports three tiers. Most readers only need the **verification
tier** (no API key, no raw data).

---

## System Requirements

- **Python** 3.11+ with `numpy` and `matplotlib` (`pip install -r requirements.txt`)
- **LaTeX** with `pdflatex` + `bibtex` (TeX Live or MiKTeX) to rebuild the PDF
- **Deep tier only:** `GEMINI_API_KEY` in the environment, plus the public raw
  corpora (see `DATA_SOURCES.md`)

---

## Tier 1 — Verification (no API key, no raw data)

Every macro, table, figure, and the PDF regenerate from the committed
`reports/`:

```bash
pip install -r requirements.txt

# 1. macros (single source of truth for every number in the prose)
python scripts/generate_paper_variables.py        # -> latex/variables.tex

# 2. tables
python scripts/generate_validity_table.py
python scripts/generate_replication_table.py
python scripts/generate_crossmodel_table.py
python scripts/generate_h5_table.py
python scripts/generate_supplementary_tables.py

# 3. figures
python scripts/generate_figures.py                # -> latex/figures/*.pdf (needs data/joined.csv; see Tier 2)

# 4. PDF
cd latex
pdflatex -interaction=nonstopmode main && bibtex main \
  && pdflatex -interaction=nonstopmode main && pdflatex -interaction=nonstopmode main
```

Output: `latex/main.pdf`. The figure step needs the joined table; the two
figures shipped under `latex/figures/` are pre-built, so the PDF rebuilds
without re-running Tier 2.

---

## Tier 2 — Analysis (rebuild `reports/` from the corpora + predictions)

Restore the locked corpora and the harness predictions, then recompute the
aggregated artifacts.

```bash
# A. restore + verify the corpora (see DATA_SOURCES.md for downloads + hashes)
python scripts/01_ingest_upworthy.py --input data/upworthy_raw/upworthy-exploratory.csv
python scripts/build_mind_corpus.py
python scripts/build_reddit_corpus.py

# B. (predictions) either restore data/predictions/ or regenerate via Tier 3

# C. join + statistics  (all paper numbers flow from these)
python scripts/03_build_joined.py
python scripts/compute_validity.py
python scripts/analyze_replication.py
python scripts/analyze_h003.py
python scripts/error_analysis.py
python scripts/analyze_baseline_ties.py
python scripts/power_analysis.py
```

Then re-run Tier 1 to regenerate the macros/tables/figures from the refreshed
`reports/`.

---

## Tier 3 — Deep (re-run the LLM harness end to end)

Regenerate the raw per-persona predictions. Requires `GEMINI_API_KEY`.

```bash
export GEMINI_API_KEY="<your-key>"   # value is never printed by the scripts

# PRIMARY: significant subset, persona panel (3 draws) + no-persona baseline (30 draws)
python scripts/run_predictions.py --models gemini-3.1-flash-lite --significant-only --packages 0 --draws 3  --seed 42 --out-suffix=-sig3
python scripts/run_predictions.py --baseline --models gemini-3.1-flash-lite --significant-only --packages 0 --draws 30 --seed 42 --out-suffix=-baseline
python scripts/run_predictions.py --models gemini-3.1-flash-lite --packages 0 --draws 1 --seed 42 --out-suffix=-full

# Cross-tier robustness: repeat with --models gemini-2.5-flash and gemini-3.5-flash
# Replication splits: pass --corpus datasets/<name>-<date>.json with the matching --out-suffix

# validate the produced predictions against the schema before joining
python scripts/02_run_personas.py --validate-only
```

Then continue with Tier 2 (join + statistics) and Tier 1 (assets).

---

## Reference Results

| Metric | Persona panel (P=10) | No-persona baseline | Notes |
| :--- | :---: | :---: | :--- |
| Kendall τ | 0.084 [0.020, 0.147] | **0.361 [0.289, 0.430]** | within-package rank concordance |
| Top-1 accuracy | 34.6% | **49.2%** | predicted #1 == real #1 |
| Reliable packages | 399 | 399 | statistically distinguishable winner |
| Variants | 1,494 | 1,494 | |
| Cross-family (gpt-4.1) baseline τ | — | 0.300 | top-1 49.1% |

The headline result: **persona conditioning degrades predictive validity** —
the no-persona baseline outranks the persona panel with non-overlapping CIs.

---

## Validation & audits (pre-submission)

```bash
# citation integrity (authorship via Crossref/arXiv) — confirm Upworthy DOI authors
python <path-to>/validate_citations.py --tex-root latex --bib latex/references.bib --crossref

# reproducibility audit (orphan floats / undefined refs)
python <path-to>/audit_latex_refs.py latex
```

---

## Troubleshooting

- **`predictions artifact missing`** — Tier 1 doesn't need predictions; for Tiers 2–3 restore `data/predictions/` or run Tier 3.
- **Corpus hash mismatch** — re-download the raw source and re-run the ingest script; the manifest `corpus_sha256` is deterministic under `--seed 42`.
- **`GEMINI_API_KEY not found`** — export it in the environment (Tier 3 only); the scripts never print the value.

---

## Citation

```text
Maiorano, A. C. (2026). Do Synthetic Personas Predict Real Audience Response?
A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based Copy
Simulation. Preprint.
```
