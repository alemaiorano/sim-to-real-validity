# Do Synthetic Personas Predict Real Audience Response?

Local correction draft of arXiv:2609.25010, based on public release
`7c1ab46b5d881529b79769fb870ed1f2fb98619c`.

The original tables match their stored reports. The audit found errors in metric naming,
winner selection, denominator reporting, and interpretation. This revision preserves the
historical reports, supplies corrected analysis code and a separate historical GPT-4.1 diagnostic,
and adds a matched-budget Gemini/GPT-4.1 collection with retained raw responses.
It has not been submitted as a new arXiv version.

- Historical Upworthy estimates favor the generic baseline; the reported rank coefficient
  is Goodman–Kruskal gamma, **not Kendall tau**.
- Reddit panel top-1 and lift exceed the baseline. Claims of dominance everywhere were wrong.
- Corrected GPT-4.1 analysis retains a positive paired baseline gap, conditional on stored
  post-parser scores and unequal budgets. It is retrospective, not independent replication.
- The primary new comparison favors the baseline in valid rank comparisons, expected top-1
  and lift. A post-hoc sensitivity excludes the archive's documented randomization-risk period:
  top-1/lift gaps remain positive, but Gemini tau-b and Spearman intervals include zero.
  Bottom-1 intervals include zero in both models. Counts and paired
  intervals are in the new tables, with all exclusions disclosed.
- Historical Gemini observations remain unavailable. Their corrected estimates are **not established**.

New generations are a separate experiment on the corrected exploratory cohort, with thirty
observations per arm and variant within each model. The separate replication bundle retains
requests, response bytes, exact inputs, coverage, per-package metrics, source history and the
recovered original GPT checkpoint. Historical Gemini generations remain unrecovered.

The [full-text audit](docs/audit/full-text-claim-ledger.json) traces every paragraph and caption
to evidence and distinguishes historical limits from implemented corrections.

The revised [PDF](latex/main.pdf) explains the evidence tiers and limitations at first reading.
[Correction record](docs/archive/changes/2026-10-31-paper-corrections.md) maps the audit findings
to changes and remaining gaps. [Accepted plan](docs/audit/plan-v3.txt) and
[Astra consensus](docs/audit/astra-consensus.txt) document the proposal review.

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
