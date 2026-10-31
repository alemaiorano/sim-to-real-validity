# Do Synthetic Personas Predict Real Audience Response?

Local correction draft of arXiv:2609.25010, based on public release
`7c1ab46b5d881529b79769fb870ed1f2fb98619c`.

The original tables match their stored reports. The audit found errors in metric naming,
winner selection, denominator reporting, and interpretation. This revision preserves the
historical reports and supplies corrected analysis code and a separate partial GPT-4.1 diagnostic.
It has not been submitted as a new arXiv version.

- Historical Upworthy estimates favor the generic baseline; the reported rank coefficient
  is Goodman–Kruskal gamma, **not Kendall tau**.
- Reddit panel top-1 and lift exceed the baseline. Claims of dominance everywhere were wrong.
- Corrected GPT-4.1 analysis retains a positive paired baseline gap, conditional on stored
  post-parser scores and unequal budgets. It is retrospective, not independent replication.
- Historical Gemini observations remain unavailable. Their corrected estimates are **not established**.

The revised [PDF](latex/main.pdf) explains the limitations at first reading.
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
python -m unittest discover -s tests -v
```

Historical inputs are hash-pinned in `reports/legacy-provenance.json`. Corrected analyses
require new destinations and refuse to overwrite historical reports. Statistical runtime uses
the Python standard library; figure generation and null-screen tests use NumPy/Matplotlib.
SciPy is an optional test oracle. No provider experiments were run for these corrections.

The study harness is separate from any commercial product. Code: MIT. Aggregated artifacts:
CC BY 4.0. Third-party corpora and recovered raw checkpoints are not redistributed.
