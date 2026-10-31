# Replication and verification

For exact primary-report reproduction use CPython 3.12.3 on Linux/WSL
(the collector/replay imports POSIX `fcntl`),
`pip install -r requirements.txt`; PDF compilation also needs
`pdflatex` and `bibtex`. Run commands from the repository root.

## 1. Reexport reports and build the PDF

The public Git package supports this section without a private checkpoint or raw corpus:

```bash
make verify
make reproduce
make verify
make test
```

`REPLICATION_SHA256SUMS` covers the listed versioned payload; Git records the checksum file.
The Makefile delegates to the existing exporter scripts and does not add another metric engine.
For the raw replay commands in sections 2 and 4–5, restore the separate companion first; it is
not included as Git blobs or provided by a public download URL in this package.

Run the exporters listed in README. They verify hashes before reading historical reports.
`generate_reanalysis_assets.py` separately reads the committed historical GPT derivative and selection
diagnostic. `generate_recollection_assets.py` reads the primary raw-backed matched-experiment reports,
verifies their hashes and plan identity, and refuses unfinished observations. This verifies displayed numbers, not all original raw observations.

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

### CSV ingestion and exact locked inputs

Saved experiments use the exact `matched-v2/inputs/corpus.json` with the documented hash.
Do not replace it by rerunning an ingester when replaying existing generations. The source at
`1326962cd6e3b4bb41f889737ffcbc8516655171` reconstructs the locked text preprocessing:
it removed embedded linebreaks before parsing CSV. One of 6,978 retained headlines is affected
(package `5429d6e75f7828ebff000066`, variant `#3`); it is outside both selected cohorts.
Every click/impression/rate and both selected-ID sets match the newline-aware source CSV.

The current `01_ingest_upworthy.py` preserves quoted multiline CSV fields. Fresh ingestion
therefore yields a newline in that one headline; it is a new derivative, not the exact input
for existing scores. Use a new output directory and future collection plan for any new input.
The preserved source history, original corpus and response journals remain authoritative for
existing results. No scientific result is silently regenerated from changed headline text.

## 2. Offline GPT checkpoint replay and analysis

The recovered checkpoint is included in the separate replication bundle at
`historical-gpt41/checkpoint.jsonl`; it is not a Git repository blob. Required SHA256 values:

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

## 3. Analyze supplied predictions with explicit metric identities

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

## 4. Primary matched-budget experiment: replay without API calls

The primary and supplementary comparisons have separate collection protocols. Primary
observations do not reconstruct missing supplementary Gemini generations.
The frozen protocol is `paired-raw-retained-v2`, source commit
`cba15e9cd676ba9c871f873e1b6ad3bc7b094996`, with the explicit content-filter continuation
amendment at `b1836a5de5ae727e7650b82a4f1bc38039ee6556`. The original plan and pre-amendment
Azure bytes remain unchanged and are preserved as a snapshot. Use the **final source bundle**
for replay of the amended Azure chain; the earlier collector bundle cannot read its new marker.
The standalone replication bundle contains:

- `matched-v2/`: exact corpus/CSV/panel, frozen observation and request plans, and raw journals.
- `matched-v2/snapshots/`: immutable raw bytes used by each report.
- `derived/`: final raw-replay reports and reviewer CSVs with response hashes, variant means,
  package metrics, coverage, and exclusions.
- `historical-gpt41/`: recovered original scalar checkpoint and historical replay evidence.
- `matched-v1/`: compatibility probes, explicitly excluded from the scientific results.
- Git bundles containing frozen collection source and final paper/exporter source.
- `ARTIFACT_README.txt`, validation evidence, file checksum manifest and archive checksum.

Verify the archive checksum before extraction, then run `sha256sum -c SHA256SUMS` from the
extracted artifact root. Restore source with `git clone --branch
research/public-review-disclosure-2026-10-31 SOURCE_FINAL.bundle source` (substitute the actual
bundle path). Work from `source`; the original pinned producer is available in its history.
Use the recorded CPython 3.12.3 environment. Floating-point `sum` changed in Python 3.12;
older interpreters are not asserted to reproduce exact ranks/bytes. Set a shell variable to the extracted artifact directory:

```bash
ARTIFACT_ROOT=/absolute/path/to/extracted/artifact
python scripts/analyze_recollection.py --run-dir "$ARTIFACT_ROOT/matched-v2" \
  --backend gemini --output /new/path/gemini.json
python scripts/analyze_recollection.py --run-dir "$ARTIFACT_ROOT/matched-v2" \
  --backend azure --output /new/path/azure.json
cmp /new/path/gemini.json "$ARTIFACT_ROOT/derived/gemini.json"
cmp /new/path/azure.json "$ARTIFACT_ROOT/derived/azure.json"
python scripts/export_recollection_observations.py --run-dir "$ARTIFACT_ROOT/matched-v2" \
  --backend gemini --report /new/path/gemini.json --output-dir /new/path/gemini-reviewer
python scripts/export_recollection_observations.py --run-dir "$ARTIFACT_ROOT/matched-v2" \
  --backend azure --report /new/path/azure.json --output-dir /new/path/azure-reviewer
python scripts/generate_recollection_assets.py
```

Replay verifies the input hashes, allocation, sent requests, journal hash chain, exact response
bytes, choice indices, strict parsing and token accounting. Its primary package policy requires
all 30 planned scores in each arm for every variant; failed observations and exclusions remain
visible. Score budgets are matched **within model**. Azure requested three choices per call
symmetrically in both arms; Gemini requested one. Choices are not presumed independent.
The report intervals resample packages and condition on selection and recorded generations.
Available-observation sensitivity has different coverage and must not replace the primary result.

Exact request bodies are authoritative for generation parameters. Both backends explicitly
send temperature 0.8 and a request seed. Neither backend explicitly sets top-p or frequency /
presence penalties; no fixed numerical provider default is asserted. Gemini's thinking level
is MINIMAL. Azure sends three choices per request symmetrically in both arms. The complete
first-person, third-person and baseline prompt strings are in the versioned collector and
retained requests, not inferred from the illustrative appendix template.

No API key is needed for these operations. The frozen plan includes historical absolute backup
locations as provenance; offline replay does not require those directories. Blank reviewer CSV
scores/metrics are missing/undefined, never imputed zero. Raw journals retain errors and retries. An Azure `content_filter` /
`ResponsibleAIPolicyViolation` refusal remains terminal missing and is never retried or rewritten.
The explicit mirrored amendment pins the original prefix, source and unchanged scientific
allocation; a new journal marker records its application. Other permanent errors retain global
stops. Content-dependent exclusions and the pause are disclosed; no comparative performance
was used to choose this amendment.

## 5. Post-hoc randomization-window sensitivity

The frozen primary experiment predates this audit finding. Its inputs and results stay unchanged.
The archive's 2024 author correction identifies a risk period, not an LLM-generation failure.
Use the saved complete primary variant means with their raw/report/plan hash lineage:

```bash
python scripts/analyze_randomization_window.py --run-dir "$ARTIFACT_ROOT/matched-v2" \
  --derived-dir "$ARTIFACT_ROOT/derived" --output /new/path/window_sensitivity.json
cmp /new/path/window_sensitivity.json recollection/2026-10-31/window_sensitivity.json
python scripts/generate_window_sensitivity_assets.py
```

The rule excludes an entire experiment if any source row's original calendar date is between
2013-06-25 and 2014-01-10 inclusive. The archive timezone is undocumented; no timezone is invented.
Missing date mappings, duplicate variant/arm rows, changed primary masks, missing primary draws,
and incompatible input/report hashes are rejected. All six paired metrics are reported, with
valid IDs and counts. The sensitivity was chosen after a literature correction was identified;
it is explicitly post hoc and supplies no independent replication or causal guarantee.

## 6. Future paid collection

Future generations create a new experiment and require a new plan/run directory. Provider aliases,
best-effort seeds, quota and infrastructure can change. The current `recollect.py prepare` freezes
these study-specific inputs and checks their hashes; `collect` uses only an explicitly supplied
environment file. It supports bounded retries, durable response retention, fixed costs and
rate limits. Review source/configuration against the actual provider before a new paid session.
Never merge future observations into this checkpoint or historical scalar files. Credentials
are excluded from the replication bundle. `run_predictions.py` and `tier2_crossmodel.py` are
separate harnesses with different protocols; they do not reproduce this collection.

## Checks

`python -m unittest discover -s tests -v` uses real producers/consumers with stubbed transports.
It checks metrics, tied extrema, paired denominators, null screening, parsing, aggregation,
checkpoint isolation, artifact immutability, and output collisions. Optional SciPy checks tau-b.
