# Research Replication Guide

Replication package for [the arXiv preprint](https://arxiv.org/abs/2609.25010),
DOI [10.48550/arXiv.2609.25010](https://doi.org/10.48550/arXiv.2609.25010).
Run all commands from the repository root, preferably in a disposable clone
when recomputing results. Python 3.11+ and `pip install -r requirements.txt`
provide the analysis dependencies. PDF builds also need `pdflatex` and `bibtex`.

## Tier 1 — Verify tables and rebuild the PDF

This path needs no API keys or raw-data downloads. It reexports the committed
result artifacts and uses the included figures to rebuild the manuscript.
It does not independently recompute the statistics from raw observations.

```bash
python scripts/generate_paper_variables.py
python scripts/generate_validity_table.py
python scripts/generate_replication_table.py
python scripts/generate_crossmodel_table.py
python scripts/generate_pilot_table.py
python scripts/generate_h5_table.py
python scripts/generate_supplementary_tables.py

cd latex
pdflatex -interaction=nonstopmode main && bibtex main \
  && pdflatex -interaction=nonstopmode main && pdflatex -interaction=nonstopmode main
```

The output is `latex/main.pdf`. To regenerate only the comparison figure from
`reports/baseline_comparison.json`, without downloading a corpus:

```bash
python scripts/generate_figures.py --comparison-only
```

The reliability histogram needs the restored Upworthy exploratory corpus:
`datasets/upworthy-subset-2026-06-03.json`. After following `DATA_SOURCES.md`,
`python scripts/generate_figures.py` regenerates both numerical figures.
The protocol diagram is the included `latex/figures/protocol.tex`.

## Tier 2 — Recompute statistics from corpus and predictions

Restore and hash-check the corpus as described in `DATA_SOURCES.md`. Restore
historical predictions if you have them, or collect new predictions via Tier 3.
The primary persona file is `data/predictions/gemini-3_1-flash-lite-sig3.jsonl`.
The runner, validator, join and error analysis use this same file by default.

```bash
python scripts/02_run_personas.py --validate-only
python scripts/03_build_joined.py
python scripts/compute_validity.py
python scripts/analyze_h003.py
python scripts/error_analysis.py
python scripts/analyze_baseline_ties.py
python scripts/analyze_h5_aggregation.py
```

To analyze another model or split, select its file explicitly:

```bash
python scripts/02_run_personas.py --validate-only --predictions <prediction-file.jsonl>
python scripts/03_build_joined.py --predictions <prediction-file.jsonl> --corpus <corpus.json>
```

`compute_validity.py` analyzes only the joined predictions supplied. Joining
only the significant subset cannot reproduce the published all-package
sensitivity analysis. The latter requires the corresponding historical
all-package predictions. Raw historical predictions are not included here.

For replication, restore all five corpora and the corresponding persona and
baseline files before `python scripts/analyze_replication.py`. Exact filenames
are listed in its `DSETS` mapping; missing datasets are explicitly skipped.
Do not replace the committed five-dataset report with a partial run.

The historical summaries `baseline_comparison.json`, `cross_model_gap.json`
and `stability.json` have no dedicated recomputation script in this package.
They remain inputs to the verification exporters. Likewise, `power_analysis.py`
is an earlier planning calculation (its recorded primary n is 124), not a
runner that updates the final sample size. These limits also exist in the
original research tree; the package does not claim a complete raw-to-report
rebuild of every historical artifact.

## Tier 3 — Collect new Gemini predictions

This tier calls paid provider APIs. Supply your own key through
`GEMINI_API_KEY` or a local, gitignored `.env`. Corpus files must already exist.
Use the recorded experimental configuration when comparing with the paper;
provider availability and model changes can prevent exact historical replay.
A fixed seed does not guarantee identical generations across provider updates.

```bash
export GEMINI_API_KEY="<your-key>"

# Primary panel: all significant-winner packages, 3 draws per persona.
python scripts/run_predictions.py --models gemini-3.1-flash-lite --significant-only --packages 0 --draws 3 --seed 42 --out-suffix=-sig3
# Primary no-persona baseline: 30 draws per variant.
python scripts/run_predictions.py --baseline --models gemini-3.1-flash-lite --significant-only --packages 0 --draws 30 --seed 42 --out-suffix=-baseline
# All-package, single-draw run used by the exploratory replication condition.
python scripts/run_predictions.py --models gemini-3.1-flash-lite --packages 0 --draws 1 --seed 42 --out-suffix=-full

python scripts/02_run_personas.py --validate-only
```

Cross-tier runs use the paper's other recorded Gemini models. Other datasets
use `--corpus` and the output suffixes expected by `analyze_replication.py`.
Checkpoint reuse is valid only for the same model, corpus, prompt variant,
seed, temperature and draw configuration; use distinct suffixes for new runs.

## Cross-family replication — Azure OpenAI

`scripts/tier2_crossmodel.py` is the original GPT-4.1 study runner adapted to
standalone paths. It reuses the Gemini harness's prompt builder/parser and the
same ranking metrics, keeping the experimental comparison unchanged.
Credentials and endpoint are supplied only through environment variables;
no external credential files or product services are read.

```bash
export AZURE_OPENAI_API_KEY="<your-key>"
export AZURE_OPENAI_BASE_URL="<your-resource-base-url>"
export AZURE_OPENAI_DEPLOYMENT="<your-gpt-4.1-deployment>"
python scripts/tier2_crossmodel.py --draws 3 --baseline-draws 10 --temperature 0.8
```

The default outputs are checkpoints and an `upworthy_<deployment>.json`
summary under the gitignored `data/predictions/crossfamily/`. `--output-dir`
can select another local directory. The summary includes persona/baseline
metrics and paired per-package gaps, matching the structure of
`reports/crossfamily_gpt41.json`. The runner does not overwrite that published
artifact. A new provider run is a new experiment, not proof that the archived
result has been reproduced exactly.

## Local checks

```bash
python -m unittest discover -s tests -v
```

The tests exercise the real producer/validator/join with stubbed provider
transports and temporary synthetic corpora. They need no keys or network.
