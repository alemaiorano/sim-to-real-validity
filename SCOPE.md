# Artifact Scope — Sim-to-Real Validity of Persona-Based Copy Simulation

Replication package for the paper *"Do Synthetic Personas Predict Real Audience
Response? A Sim-to-Real Study Where a No-Persona Baseline Beats Persona-Based
Copy Simulation."*

This package is **verification-grade and harness-included**: every numerical
macro and table can be reexported from the shipped result
artifacts. The PDF uses the included figures; regenerating the reliability
histogram additionally requires the public Upworthy corpus. Gemini and Azure
OpenAI study runners are included. Reexporting a report is distinct from
recomputing it from historical raw observations.

## Reproducibility tiers

| Tier | What it reproduces | Needs |
|---|---|---|
| **Verification** | macros, tables and PDF using included figures; comparison figure from its report | committed `reports/`, included figures + Python + LaTeX. No API key, no raw data. |
| **Analysis** | statistics supported by the shipped analysis scripts | restored corpora + historical predictions or new provider runs. Historical rebuild limits are listed in `REPLICATION.md`. |
| **Deep** | new per-persona/baseline predictions under the recorded protocol | public corpora + Gemini or Azure OpenAI credentials. New runs need not match historical generations. |

## Why the harness *is* included (unlike a product replication)

The persona simulation evaluated here is a **study-specific, self-contained
harness** — `scripts/run_predictions.py` calls Gemini directly with the fixed
panel in `data/persona_panel.json` and an inline prompt template.
`scripts/tier2_crossmodel.py` repeats that protocol on Azure OpenAI and reuses
the same prompt builder, parser and ranking metrics. Both runners operate
independently of product databases, orchestration and proprietary engines.
The method under test is the *general technique* (persona-conditioned vs.
no-persona LLM ranking), not a specific product, so it is released in full. This
is the same controlled-harness discipline used to keep the conflict-of-interest
mitigation honest (see the paper's Ethics statement).

## Included

| Path | Contents | Why it is safe |
|---|---|---|
| `latex/` | LaTeX sources, sections, auto-generated tables/figures, `references.bib`, compiled `main.pdf` | The paper itself; public on publication |
| `scripts/` | corpus ingestion (`01_ingest_upworthy.py`, `build_mind_corpus.py`, `build_reddit_corpus.py`), the persona/baseline harness (`run_predictions.py`, `tier2_crossmodel.py`, `02_run_personas.py`), join + validity (`03_build_joined.py`, `compute_validity.py`), analyses (`analyze_*`, `error_analysis.py`, `power_analysis.py`), and all table/figure exporters (`generate_*`) | Study harness + paper-asset generation; decoupled from any product |
| `reports/` | Aggregated result artifacts: correlation, signal strength, replication, cross-model gap, error analysis, power, stability (JSON/CSV/MD) | Result numbers, not raw generations; back every paper claim |
| `data/persona_panel.json` | The fixed, versioned ten-persona panel (system under test) | Authored from public demographics; not reused from any product |
| `datasets/*.manifest.json` | Locked corpus manifests (source + corpus sha256, sampling seed/params) | Provenance only; the corpora are public and regenerable |
| `tests/` | Offline producer/consumer and credential-boundary regression checks | Temporary synthetic inputs and stubbed provider transports |
| root | `README.md`, `SCOPE.md`, `REPLICATION.md`, `DATA_SOURCES.md`, `CLAIMS_TO_ARTIFACTS.csv`, `CITATION.cff`, `LICENSE`, `LICENSE-DATA.md`, `requirements.txt` | Documentation and metadata |

## Excluded — bulky / regenerable / not redistributable

| Item | Reason |
|---|---|
| `data/sim_predictions.jsonl`, `data/predictions/`, `data/joined.csv` | Historical per-persona observations and joined tables are not included. New runs can collect the same kind of data but are not guaranteed to recreate it exactly. Aggregated reports support the verification path. |
| `data/upworthy_raw/`, `data/mind_raw/`, `data/reddit_raw/` | Raw third-party corpora — public but not re-hosted. Retrieve + verify via `DATA_SOURCES.md` and the committed manifests. |
| `datasets/*-subset-*.json` (locked corpora) | Large derived corpora; regenerate deterministically from the raw source with the ingest scripts (each must match its manifest `corpus_sha256`). |
| `.env` | API keys / secrets. Set `GEMINI_API_KEY` in the environment for the deep tier. |
| Internal experiment plans, product implementation and credential configuration | They are not inputs to this paper's controlled study and are unnecessary for replication. |

## Consequence for re-derivation

- The PDF rebuilds fully from the shipped sources + `reports/` (verification tier).
- `generate_paper_variables.py` and the `generate_*_table.py` / `generate_figures.py`
  exporters regenerate the macros, tables and comparison figure from `reports/`.
  The reliability figure instead reads the restored Upworthy corpus.
- Recomputing statistics needs the corresponding corpora and raw predictions.
  Some historical reports lack dedicated recomputation scripts in the original
  tree and this package. See `REPLICATION.md` for the supported paths and limits.

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
├── tests/                   offline regression checks
├── reports/                 aggregated result artifacts (every paper number)
├── data/persona_panel.json  the fixed persona panel (SUT)
└── datasets/                corpus manifests (provenance)
```
