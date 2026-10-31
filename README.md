# Do Synthetic Personas Predict Real Audience Response?

Version 2 working manuscript for arXiv:2609.25010. The study compares a fixed ten-persona
panel with a generic-reader baseline in a matched-budget Gemini/GPT-4.1 experiment. Exact raw
responses, plans, coverage, metric-specific paired IDs and offline replay are retained.
This local version has not been submitted or publicly deposited.

The primary comparison favors the baseline on valid ranks, expected top-1 and captured lift.
A post-hoc exclusion of Upworthy's documented randomization-risk period retains positive
top-1/lift contrasts, while Gemini tau-b and Spearman intervals include zero. Bottom-1
intervals include zero in both models. Archived Reddit decision metrics favor the panel.
Results concern the specified panel/cohort/protocol and do not identify a causal mechanism.

Supplementary archived aggregates and the retrospective GPT-4.1 scalar diagnostic retain
their own budgets, screen and tie semantics. Historical Gemini observations and original
GPT response texts remain unavailable. New generations are a separate experiment.

The [PDF](latex/main.pdf) presents the methods and their limitations as a standalone study.
The [source-driven evidence ledger](docs/audit/full-text-claim-ledger.json) traces its text
and captions. Earlier [method/provenance records](docs/archive/changes/2026-10-31-paper-corrections.md),
[accepted plan](docs/audit/plan-v3.txt) and [Astra consensus](docs/audit/astra-consensus.txt)
remain preserved outside the paper. Formula checks and the DoesItStand execution are recorded
in the [v2 changeset](docs/archive/changes/2026-10-31-paper-v2-formula-review.md).

## Reproduction

See [REPLICATION.md](REPLICATION.md). Reexport requires no API or private checkpoint:

```bash
python scripts/generate_paper_variables.py
python scripts/generate_validity_table.py
python scripts/generate_replication_table.py
python scripts/generate_crossmodel_table.py
python scripts/generate_pilot_table.py
python scripts/generate_h5_table.py
python scripts/generate_supplementary_tables.py
python scripts/generate_reanalysis_assets.py
python scripts/generate_recollection_assets.py
python scripts/generate_window_sensitivity_assets.py
python -m unittest discover -s tests -v
```

Historical inputs are hash-pinned in `reports/legacy-provenance.json`. Corrected analyses
require new destinations and refuse to overwrite historical reports. Statistical runtime uses
the Python standard library; figure generation and null-screen tests use NumPy/Matplotlib.
SciPy is an optional test oracle. The new raw-backed experiment was collected separately from
all historical checkpoints. Exact recomputation uses saved response bytes and requires no API call.
Provider aliases and seeds do not guarantee identical future generations.

The study harness is separate from any commercial product. Code: MIT. Aggregated artifacts:
CC BY 4.0. Large raw evidence and the exploratory inputs are retained in a separate replication
bundle rather than committed as Git blobs. This local revision and its bundle have not been
publicly published or submitted.

[Retention and recovery](RETENTION.md) documents versioned OneDrive copies, protected local
vaults, checksum verification and the exercised restore drill.
