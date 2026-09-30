# sim-to-real-validity 🎯

[![License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Paper: arXiv](https://img.shields.io/badge/arXiv-2609.25010-b31b1b)](https://arxiv.org/abs/2609.25010)

> **Do synthetic personas predict real audience response? An artifact-first sim-to-real validity study.**

This repository is the **public replication package** for the research paper:

**"Do Synthetic Personas Predict Real Audience Response? A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based Copy Simulation"**.

[Read the preprint](https://arxiv.org/abs/2609.25010) ·
[DOI: 10.48550/arXiv.2609.25010](https://doi.org/10.48550/arXiv.2609.25010).

Every numerical macro and table regenerates from the versioned result
artifacts. The PDF rebuilds using the included figures; regenerating the
reliability figure also needs the public Upworthy corpus. Both the Gemini
and Azure OpenAI study harnesses are included, together with the fixed
persona panel. Raw per-persona generations are not redistributed.

---

## 🎯 Core Contributions

Marketers increasingly use LLMs as "synthetic personas" to predict how an
audience will react to copy before it ships. This paper tests whether that
prediction is **valid against real behaviour**, and whether the persona
machinery actually helps, along three lines:

1. **Held-out ground truth.** The [Upworthy Research Archive](https://osf.io/jd64p/)
   (Matias et al., *Scientific Data* 2021): thousands of headline A/B tests
   shown to the *same* real traffic, giving a within-package relative-ranking
   ground truth robust to absolute-scale differences.
2. **A controlled harness, not a product.** A fixed ten-persona panel grounded
   in the real audience's demographics (Pew/Holcomb 2013) vs. a no-persona
   zero-shot baseline that simply asks the model how likely a typical reader is
   to click. Same model, same corpus, same metrics.
3. **Artifact-first evaluation.** Bootstrap confidence intervals, three
   independent Upworthy splits, a cross-domain news replication, and a
   cross-model-family check (OpenAI gpt-4.1) — all regenerated from versioned
   result artifacts under `reports/`.

---

## 🚀 Quick Start

Every numerical macro and table regenerates from the committed artifacts in
`reports/`. **No API keys or raw-data downloads are required to rebuild the
PDF with the included figures.**

### Prerequisites
- Python ≥ 3.11 (`pip install -r requirements.txt` → numpy, matplotlib)
- A LaTeX distribution with `pdflatex` + `bibtex` (TeX Live or MiKTeX) to rebuild the PDF

### Reproduce the paper assets (no API key)
```bash
git clone https://github.com/alemaiorano/sim-to-real-validity.git
cd sim-to-real-validity
pip install -r requirements.txt

# re-derive every macro and table from the committed result artifacts
python scripts/generate_paper_variables.py
python scripts/generate_validity_table.py
python scripts/generate_replication_table.py
python scripts/generate_crossmodel_table.py
python scripts/generate_pilot_table.py
python scripts/generate_h5_table.py
python scripts/generate_supplementary_tables.py

# rebuild the PDF
cd latex && pdflatex -interaction=nonstopmode main && bibtex main \
  && pdflatex -interaction=nonstopmode main && pdflatex -interaction=nonstopmode main
```

Output: `latex/main.pdf`. To regenerate the analysis artifacts themselves
(`reports/*.json`) or re-run the LLM harness from scratch, see
[`REPLICATION.md`](REPLICATION.md). See [`SCOPE.md`](SCOPE.md) for exactly what
is and is not included.

---

## 📊 Empirical Evidence

The package reproduces the paper's headline result: on the reliable subset of
A/B tests (those with a statistically distinguishable winner), **persona
conditioning degrades predictive validity** — the no-persona baseline ranks
variants markedly better, with non-overlapping confidence intervals.

| Finding | Persona panel (P=10) | No-persona baseline |
| :--- | :---: | :---: |
| **Kendall τ (rank concordance)** | 0.084 [0.020, 0.147] | **0.361 [0.289, 0.430]** |
| **Top-1 accuracy** | 34.6% | **49.2%** |
| Reliable packages (n) | 399 | 399 |
| Variants | 1,494 | 1,494 |

Robustness: the direction replicates across three independent Upworthy splits,
holds on a different-domain news dataset (MIND), and reproduces on a different
model family (OpenAI gpt-4.1: baseline τ = 0.300, top-1 49.1%) with a
significant paired gap. **Takeaway:** for predicting aggregate engagement, a
plain LLM ranker beats persona simulation.

---

## 🔬 Research & Replication

This repository is a **verification-grade, harness-included** artifact package:

- **`latex/`** — LaTeX manuscript sources with auto-generated tables/figures, `references.bib`, and the compiled `main.pdf`.
- **`scripts/`** — corpus ingestion, Gemini (`run_predictions.py`) and Azure OpenAI (`tier2_crossmodel.py`) study harnesses, validity statistics, error analysis, and table/figure exporters.
- **`reports/`** — versioned aggregated result artifacts (correlation, signal strength, replication, cross-model gap, error analysis). These support the paper's numerical claims.
- **`data/persona_panel.json`** — the fixed, versioned ten-persona panel (the system under test).
- **`datasets/*.manifest.json`** — locked corpus manifests (sha256 + sampling params) for provenance; the corpora themselves are public and regenerable, not re-hosted.
- **`SCOPE.md`** — artifact scope and IP boundary (what is included, excluded, and why).
- **`CLAIMS_TO_ARTIFACTS.csv`** — claim-by-claim map from the paper to the backing artifacts.
- **`DATA_SOURCES.md`** — retrieval + checksum instructions for the public corpora.

### Basic reproduction command
```bash
python scripts/generate_paper_variables.py && python scripts/generate_validity_table.py
```

### Artifact-first contract (enforced by the scripts)
1. No hand-edited numbers — every macro in `latex/variables.tex` is regenerated from `reports/*.json`.
2. No hand-edited tables — every `latex/tables/*.tex` is a script output.
3. No orphan floats — every `\label` is `\ref`'d in the body.
4. Missing data is a hard blocker — scripts fail loudly, never synthesize placeholders.

---

## 📄 Citation

If you use this package or the sim-to-real validity protocol, please cite our work:

```text
Maiorano, A. C. (2026). Do Synthetic Personas Predict Real Audience Response?
A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based Copy
Simulation. arXiv:2609.25010. https://doi.org/10.48550/arXiv.2609.25010
```

## 📄 License

- Code and scripts: MIT License (see `LICENSE`).
- Aggregated artifacts, persona panel, manifests, generated figures/tables: CC BY 4.0 (see `LICENSE-DATA.md`).
- The Upworthy / MIND / SNAP-Reddit corpora are third-party and are not redistributed here — see `DATA_SOURCES.md`.
