# Artifact scope

This is a correction draft of the original research release at
`7c1ab46b5d881529b79769fb870ed1f2fb98619c`.

| Evidence tier | Supported | Limit |
|---|---|---|
| Historical verification | Reexport original report values with correct gamma labels | Does not independently validate raw observations or historical valid denominators |
| Corrected offline GPT diagnostic | Recompute metrics from an exact recovered scalar checkpoint | Checkpoint not distributed; original responses absent; unequal budgets remain |
| Corrected software | New winner screen, gamma/tau-b, expected tie credit, strict parser, per-metric counts | Does not retroactively change historical generations |
| New experiments | Study-specific Gemini and Azure OpenAI collectors | Paid, user-configured, no guarantee of historical provider replay |

Included: LaTeX sources/PDF, generated assets, original aggregate reports and manifests,
corrected GPT derivatives with input hashes, fixed persona panel, analysis and collection scripts,
offline tests, audit plan/consensus, and a dated correction record.

Excluded: raw third-party corpora, original provider response texts, recovered scalar checkpoint,
credentials, commercial product code, and the monorepo's embedded paper copy.
The study harness is standalone and is not an evaluation of a deployed commercial application.

Original `reports/` artifacts and `datasets/` manifests are preserved byte for byte.
The explicit historical presentation adapter verifies their hashes before mapping mistaken
legacy field names to gamma. Corrected producers reject destinations under `reports/` and
existing output files. New corpus builders require a new directory and write a new lock date.
See REPLICATION and DATA_SOURCES for the distinction between historical restoration and corrected ingestion.

The main scientific limit is unresolved historical Gemini raw-data availability.
This revision does not certify the entire original study under corrected methods or claim
publication readiness from the plan review alone.
