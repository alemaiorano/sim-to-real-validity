# Replication and verification

Use Python 3.11+, `pip install -r requirements.txt`; PDF compilation also needs
`pdflatex` and `bibtex`. Run commands from the repository root.

## 1. Reexport reports and build the revised PDF

Run the exporters listed in README. They verify hashes before reading historical reports.
`generate_reanalysis_assets.py` separately reads the committed GPT derivative and selection
diagnostic. This verifies displayed numbers, not all original raw observations.

```bash
python scripts/generate_figures.py --comparison-only
cd latex
SOURCE_DATE_EPOCH=1793404800 pdflatex -halt-on-error -interaction=nonstopmode main
bibtex main
SOURCE_DATE_EPOCH=1793404800 pdflatex -halt-on-error -interaction=nonstopmode main
SOURCE_DATE_EPOCH=1793404800 pdflatex -halt-on-error -interaction=nonstopmode main
```

The historical screen histogram is included. To regenerate it, restore the exact original
exploratory corpus and run:

```bash
python scripts/generate_figures.py --historical-corpus /path/to/upworthy-subset-2026-06-03.json
```

## 2. Offline historical GPT replay and corrected diagnostic

The exact recovered checkpoint is **not included**. Required SHA256 values:

| Input | SHA256 |
|---|---|
| Original exploratory corpus | `523034f1fd86d4a432a57b29eb25230418dba119c3367ec04622815114cc9f85` |
| GPT-4.1 scalar checkpoint, 59,474 rows | `da6128db7ec7ead14aecd2269d25969e750f54bc1996e64c1cff78fd32614529` |

First replay the original producer, which is extracted from the pinned Git commit.
The script blocks network calls and stubs missing observations as missing; it does not
create new values. A full Git clone containing the pinned commit is required.

```bash
python scripts/replay_historical_gpt.py \
  --corpus /path/to/original-corpus.json --checkpoint /path/to/original-gpt-checkpoint.jsonl \
  --expected-corpus-sha256 523034f1fd86d4a432a57b29eb25230418dba119c3367ec04622815114cc9f85 \
  --expected-checkpoint-sha256 da6128db7ec7ead14aecd2269d25969e750f54bc1996e64c1cff78fd32614529 \
  --output /new/path/legacy-verification.json
python scripts/reanalyze_checkpoint.py \
  --corpus /path/to/original-corpus.json --checkpoint /path/to/original-gpt-checkpoint.jsonl \
  --expected-corpus-sha256 523034f1fd86d4a432a57b29eb25230418dba119c3367ec04622815114cc9f85 \
  --expected-checkpoint-sha256 da6128db7ec7ead14aecd2269d25969e750f54bc1996e64c1cff78fd32614529 \
  --output /new/path/gpt41.json
python scripts/compare_winner_filters.py --corpus /path/to/original-corpus.json \
  --output /new/path/filter-comparison.json
```

Committed derivatives are in `reanalysis/2026-10-31/`. Original response texts are absent:
stored scalar validity cannot establish whether the permissive historical parser accepted
invalid responses. The new parser cannot repair those scores retrospectively.
The analysis retains the historical 30-panel/10-baseline sampling budget.

## 3. Analyze supplied predictions with corrected estimators

```bash
python scripts/02_run_personas.py --validate-only --predictions /path/to/panel.jsonl
python scripts/03_build_joined.py --corpus /path/to/corpus.json \
  --predictions /path/to/panel.jsonl --output /new/path/joined.csv
python scripts/compute_validity.py --joined /new/path/joined.csv --output /new/path/validity.json
python scripts/analyze_replication.py --corpus /path/to/corpus.json \
  --panel /path/to/panel.jsonl --baseline /path/to/baseline.jsonl --output /new/path/comparison.json
python scripts/analyze_h5_aggregation.py --joined /new/path/joined.csv \
  --checkpoint /path/to/panel-checkpoint.jsonl --baseline /path/to/baseline.jsonl \
  --output /new/path/aggregation.json
```

Predictions must cover all variants of each analyzed package. Corrected joined files name the
winner policy. H5's `mean` gives equal weight to collapsed personas; `mean_observation` gives
equal weight to recorded draws. New summaries carry metric-specific valid and paired counts;
gamma, tau-b, and undefined values have distinct semantics.

These commands do not reconstruct missing historical Gemini observations. Some historical
summaries lack a dedicated original raw-to-report producer. Original implementations remain
accessible at the pinned Git commit, not as silent legacy branches in the corrected estimators.

## 4. New provider experiments (optional, paid)

No provider run is needed for verification above. A future run is a new experiment.
Set `GEMINI_API_KEY` or Azure OpenAI environment variables yourself; do not commit credentials.
Select an explicit corpus and approved/available provider model for your own environment.

```bash
python scripts/run_predictions.py --models MODEL_ID --corpus /path/to/corpus.json \
  --significant-only --packages 0 --draws 3 --seed 42 --out-suffix=-panel
python scripts/run_predictions.py --models MODEL_ID --corpus /path/to/corpus.json \
  --baseline --significant-only --packages 0 --draws 30 --seed 42 --out-suffix=-baseline
python scripts/tier2_crossmodel.py --corpus /path/to/corpus.json \
  --draws 3 --baseline-draws 10 --output-dir /new/path/crossfamily
```

Gemini outputs use `strict-json-v2` plus a configuration fingerprint in filenames.
GPT uses the same namespace and strict parser; its default budget remains unequal and no seed
is sent. Use a matched budget for a future matched-budget hypothesis. Configurations bind corpus,
panel, prompts, model, temperature, and sampling; terminal parse failures remain missing.
Transport errors retry within bounds. Repeated seeds do not guarantee identical provider outputs.
Revised collectors never resume historical checkpoints.

## Checks

`python -m unittest discover -s tests -v` uses real producers/consumers with stubbed transports.
It checks metrics, tied extrema, paired denominators, null screening, parsing, aggregation,
checkpoint isolation, artifact immutability, and output collisions. Optional SciPy checks tau-b.
