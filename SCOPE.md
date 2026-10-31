# Artifact scope

This is a correction draft of the original research release at
`7c1ab46b5d881529b79769fb870ed1f2fb98619c`.

| Evidence tier | Supported | Limit |
|---|---|---|
| Historical verification | Reexport original report values with correct gamma labels | Does not independently validate raw observations or historical valid denominators |
| Corrected offline GPT diagnostic | Recompute metrics from the recovered scalar checkpoint included in the separate bundle | Original response texts absent; historical unequal budgets remain |
| Corrected software | New winner screen, gamma/tau-b, expected tie credit, strict parser, per-metric counts | Does not retroactively change historical generations |
| Post-hoc period sensitivity | Recompute all six metrics outside the documented 2013--2014 risk window from saved scores | Not preregistered or independent; remaining dates are not certified defect-free; Gemini tau-b/Spearman remain uncertain |
| New matched-budget experiment | Raw-backed comparison of Gemini 3.1 Flash-Lite and GPT-4.1 on the corrected exploratory cohort | New generations; historical selection; request protocols differ across models; no broad five-dataset rerun |

Included: LaTeX sources/PDF, generated assets, original aggregate reports and manifests,
corrected GPT derivatives with input hashes, fixed persona panel, analysis and collection scripts,
offline tests, audit plan/consensus, and a dated correction record.

The separate replication bundle contains exact new response bytes, requests, the exploratory
source/corpus, and the recovered historical GPT scalar checkpoint. These large inputs are not
Git blobs. Excluded: unrecovered historical response texts, credentials, commercial product code,
and the monorepo's embedded paper copy.
The study harness is standalone and is not an evaluation of a deployed commercial application.

Original `reports/` artifacts and `datasets/` manifests are preserved byte for byte.
The explicit historical presentation adapter verifies their hashes before mapping mistaken
legacy field names to gamma. Corrected producers reject destinations under `reports/` and
existing output files. New corpus builders require a new directory and write a new lock date.
See REPLICATION and DATA_SOURCES for the distinction between historical restoration and corrected ingestion.

New Gemini generations address the reproducibility of the new experiment; they do not restore
missing historical observations. The revision does not certify all historical datasets under
corrected methods or establish general persona harm. Public scientific deposition and submission
remain separate author actions.

A separate retention runbook distinguishes protected local versions, exercised restore paths and
any independently verified offsite copy. Writable duplicates on one SSD are not offsite protection.
