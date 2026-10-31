# Public replication package scope

This repository accompanies the v2 manuscript of *Do Synthetic Personas Predict Real Audience
Response? A Headline-Ranking Study with a Generic-Reader Baseline*. The manuscript/PDF reviewed
at `25a8b2c47f0090852abbc9ad23412e91ea3bffaf` is preserved. The earlier research release is
`7c1ab46b5d881529b79769fb870ed1f2fb98619c`; archived values are retained under their own protocols.
Repository publication and submission of a new arXiv version are separate actions.

| Evidence tier | What this Git package supports | Boundary |
|---|---|---|
| Committed report reexport | Rebuild all numerical macros/tables and the PDF from versioned aggregate artifacts | Reexport does not reconstruct original model observations |
| Archived comparisons | Read original report values with explicit gamma, coverage and tie semantics | Missing original responses/valid denominators remain unavailable |
| Retrospective GPT-4.1 diagnostic | Inspect committed metrics, paired IDs, input hashes and offline replay code | Replaying the recovered scalar checkpoint requires the separate companion bundle; original response texts are absent and 30/10 budgets remain unequal |
| Matched-budget experiment | Inspect separate Gemini/GPT-4.1 reports, counts, exclusions, paired IDs and producer lineage | Full raw-byte replay requires the retained companion bundle, not this Git checkout alone |
| Post-hoc period sensitivity | Inspect all six metrics, valid IDs and provenance outside the documented risk window | Post hoc and conditional; remaining dates are not certified randomized; Gemini tau-b/Spearman intervals include zero |

## Included in Git

- Current LaTeX source/PDF, figures, generated tables and numerical macros.
- Original aggregate reports, corpus manifests and their hash-pinned provenance.
- Matched-experiment and period-sensitivity reports under `recollection/2026-10-31/`.
- Retrospective GPT metrics and diagnostics under `reanalysis/2026-10-31/`; the folder name
  describes analysis of existing scalar observations, not a separate publication category.
- The fixed persona panel, statistical/collection/replay scripts, tests and evidence ledgers.
- Citation and license metadata, reproduction commands and `REPLICATION_SHA256SUMS`.

## Separate retained companion

The complete companion holds exact exploratory inputs, raw journals including failures,
request/allocation plans, immutable snapshots, reviewer CSVs and the recovered historical GPT
scalar checkpoint. It is retained separately and is **not downloadable from this Git package**.
The repository's third-party corpus redistribution policy remains unchanged. The private backup
also contains operational retention and review evidence that is not a public dataset deposit.
Do not use a private OneDrive path as a public download link or claim full raw replay from Git alone.

Missing historical Gemini observations and GPT response texts are not replaced by new generations.
Code/prompt changes do not silently rewrite the old `reports/` files, original manifests or frozen
experiment inputs. Current analysis outputs require new destinations. The newline-aware CSV reader
creates a separate derivative; exact saved-generation replay uses its original input hash.

The study harness is separate from any deployed commercial product. Provider aliases and seeds do
not guarantee future generations. The statistical intervals condition on the selected cohorts and
recorded scores; they do not isolate a causal mechanism or show universal persona harm.
