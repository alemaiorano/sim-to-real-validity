# Do Synthetic Personas Predict Real Audience Response?

This is the **public Git replication package for the paper**:
*Do Synthetic Personas Predict Real Audience Response? A Headline-Ranking Study with a
Generic-Reader Baseline*.

[Paper PDF](latex/main.pdf) · [arXiv preprint](https://arxiv.org/abs/2609.25010) ·
[Replication guide](REPLICATION.md) · [Distribution scope](SCOPE.md) · [Citation](CITATION.cff)

This package provides the manuscript source, aggregate artifacts and executable reexport. Full raw replay additionally
requires the separately retained companion bundle; it is not downloadable from this repository.

## Reproduce from Git without API keys

Use CPython 3.12.3 on Linux/WSL, GNU Make and a LaTeX distribution providing `pdflatex`/`bibtex`
(for example, TeX Live with the article's standard packages). Exact PDF byte comparisons use the
recorded TeX Live 2023 environment; other supported toolchains can differ in PDF metadata/fonts.

```bash
git clone -c core.autocrlf=false https://github.com/alemaiorano/sim-to-real-validity.git
cd sim-to-real-validity
python3 -m pip install -r requirements.txt
make verify
make reproduce
make verify
make test
```

`make reproduce` runs the ten existing exporters and compiles the paper with the fixed
`SOURCE_DATE_EPOCH`. Included empirical figures are used unchanged; regenerating the supplementary
screen histogram requires the exact locked Upworthy corpus. `make verify` checks the listed Git
payload files against `REPLICATION_SHA256SUMS`; the Git commit identifies the checksum file itself.
`make test` exercises the offline producers and consumers with stubbed transports. No model
inference, private checkpoint, database or data download is needed for this workflow.
Python's standard library owns the statistical estimators; NumPy/Matplotlib support figures/tests.
SciPy is an optional independent test oracle. The individual commands remain in REPLICATION.md. Exact checksum verification after rebuilding
requires the recorded toolchain; a different LaTeX version can produce a different PDF even
when its numerical content agrees.

## Results and boundaries

The study compares a fixed ten-persona panel with a generic-reader baseline. The primary experiment
allocates thirty scores per arm and variant within each model. Its primary comparisons favor the
baseline on valid ranks, expected top-1 and captured lift. A post-hoc exclusion of the archive's
randomization-risk period retains positive top-1/lift contrasts, while Gemini tau-b and Spearman
intervals include zero. Bottom-1 intervals include zero in both models. Supplementary Reddit decision
metrics favor the panel. These are conditional results for the specified panel/cohort/protocol,
not a universal or causal conclusion.

| Location | Contents |
|---|---|
| `latex/` | Current paper/PDF, generated tables/macros and figures |
| `reports/` | Immutable supplementary aggregate reports |
| `reanalysis/2026-10-31/` | GPT scalar-checkpoint analysis and selection/replay provenance |
| `recollection/2026-10-31/` | Primary matched-budget reports and six-metric post-hoc period sensitivity |
| `data/persona_panel.json` | Fixed panel input |
| `datasets/*.manifest.json` | Original corpus locks and input hashes; full corpora are not Git blobs |
| `scripts/`, `tests/` | Statistical owners, exporters, collection/replay tools and offline checks |

Supplementary comparisons and the GPT checkpoint analysis retain their own budgets, screening and
tie policies. Supplementary Gemini observations, GPT checkpoint response texts and some subset lineage
remain unavailable. Primary observations and supplementary scores retain separate protocol identities. All numerical results trace to
artifacts via [CLAIMS_TO_ARTIFACTS.csv](CLAIMS_TO_ARTIFACTS.csv) and the
[source-driven evidence ledger](docs/audit/full-text-claim-ledger.json). The [native automated-review review](docs/audit/automated-review-v2-review.md) and
[technical adjudication](docs/audit/automated-review-v2-adjudication.md) are preserved separately.
Earlier methodological and review records remain under `docs/` with explicit source targets.

Code: [MIT](LICENSE). Aggregate results, fixed panel, manifests and generated assets:
[CC BY 4.0](LICENSE-DATA.md). Third-party corpora retain their own licenses and are not
redistributed here; see [DATA_SOURCES.md](DATA_SOURCES.md). The full companion and the public Git
package have distinct distribution scopes. [Retention and recovery](RETENTION.md) documents the
separately retained archive versions and tested restore procedure.
