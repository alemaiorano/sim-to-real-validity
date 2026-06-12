# Artifact Scope — Sim-to-Real Validity of Persona-Based Copy Simulation

Replication package for the paper *"Do Synthetic Personas Predict Real Audience
Response? A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based
Copy Simulation."*

This package is **verification-grade and harness-included**: every table,
figure, and number in the paper can be regenerated and checked from the
artifacts and scripts shipped here, and the simulation harness under test is
itself included.

## Reproducibility tiers

| Tier | What it reproduces | Needs |
|---|---|---|
| **Verification** | every macro, table, and figure, and the PDF | committed `reports/` + `python (numpy, matplotlib)` + LaTeX. No API key, no raw data. |
| **Analysis** | the `reports/*.json` artifacts themselves | the locked corpora (regenerate via `datasets/` manifests) + the prediction files (regenerate via the harness). |
| **Deep (end-to-end)** | the raw per-persona LLM predictions | `GEMINI_API_KEY` + the public raw corpora. The harness (`scripts/run_predictions.py`) reproduces them. |

## Why the harness *is* included (unlike a product replication)

The persona simulation evaluated here is a **study-specific, self-contained
harness** — `scripts/run_predictions.py` calls the Gemini REST API directly with
the fixed panel in `data/persona_panel.json` and an inline prompt template. It
does **not** touch any product database, orchestration, or proprietary engine.
The method under test is the *general technique* (persona-conditioned vs.
no-persona LLM ranking), not a specific product, so it is released in full. This
is the same controlled-harness discipline used to keep the conflict-of-interest
mitigation honest (see the paper's Ethics statement).

## Included

| Path | Contents | Why it is safe |
|---|---|---|
| `latex/` | LaTeX sources, sections, auto-generated tables/figures, `references.bib`, compiled `main.pdf` | The paper itself; public on publication |
| `scripts/` | corpus ingestion (`01_ingest_upworthy.py`, `build_mind_corpus.py`, `build_reddit_corpus.py`), the persona/baseline harness (`run_predictions.py`, `02_run_personas.py`), join + validity (`03_build_joined.py`, `compute_validity.py`), analyses (`analyze_*`, `error_analysis.py`, `power_analysis.py`), and all table/figure exporters (`generate_*`) | Study harness + paper-asset generation; decoupled from any product |
| `reports/` | Aggregated result artifacts: correlation, construct validity, replication, cross-model gap, error analysis, power, stability (JSON/CSV/MD) | Result numbers, not raw generations; back every paper claim |
| `data/persona_panel.json` | The fixed, versioned ten-persona panel (system under test) | Authored from public demographics; not reused from any product |
| `datasets/*.manifest.json` | Locked corpus manifests (source + corpus sha256, sampling seed/params) | Provenance only; the corpora are public and regenerable |
| root | `README.md`, `SCOPE.md`, `REPLICATION.md`, `DATA_SOURCES.md`, `CLAIMS_TO_ARTIFACTS.csv`, `CITATION.cff`, `LICENSE`, `LICENSE-DATA.md`, `requirements.txt` | Documentation and metadata |

## Excluded — bulky / regenerable / not redistributable

| Item | Reason |
|---|---|
| `data/sim_predictions.jsonl`, `data/predictions/`, `data/joined.csv` | Raw per-persona LLM generations and the joined table — large and fully regenerable from the harness + corpora. The aggregated `reports/` are the verifiable evidence. |
| `data/upworthy_raw/`, `data/mind_raw/`, `data/reddit_raw/` | Raw third-party corpora — public but not re-hosted. Retrieve + verify via `DATA_SOURCES.md` and the committed manifests. |
| `datasets/*-subset-*.json` (locked corpora) | Large derived corpora; regenerate deterministically from the raw source with the ingest scripts (each must match its manifest `corpus_sha256`). |
| `.env` | API keys / secrets. Set `GEMINI_API_KEY` in the environment for the deep tier. |
| `tier2_crossmodel.py` | Lives in the source monorepo; it writes artifacts for a *different* paper (the persona-validity-boundary study) and is not part of this package. |

## Consequence for re-derivation

- The PDF rebuilds fully from the shipped sources + `reports/` (verification tier).
- `generate_paper_variables.py` and the `generate_*_table.py` / `generate_figures.py`
  exporters regenerate every macro, table, and figure from `reports/`.
- To rebuild `reports/` from scratch (analysis/deep tiers), restore the corpora
  per `DATA_SOURCES.md`, run the harness with `GEMINI_API_KEY`, then re-run the
  analysis scripts. See `REPLICATION.md` for the exact order.

## Structure

```
sim-to-real-validity/
├── README.md
├── SCOPE.md                 (this file)
├── REPLICATION.md
├── DATA_SOURCES.md
├── CLAIMS_TO_ARTIFACTS.csv
├── CITATION.cff
├── LICENSE                  (MIT — code)
├── LICENSE-DATA.md          (CC BY 4.0 — artifacts)
├── requirements.txt
├── latex/                   paper sources + auto-generated tables/figures + main.pdf
├── scripts/                 ingestion, harness, analysis, exporters
├── reports/                 aggregated result artifacts (every paper number)
├── data/persona_panel.json  the fixed persona panel (SUT)
└── datasets/                corpus manifests (provenance)
```
