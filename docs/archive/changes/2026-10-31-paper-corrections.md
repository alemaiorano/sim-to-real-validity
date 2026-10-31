# Paper correction draft — 2026-10-31

Objective: correct the public paper's methods, labels, claims and reproduction paths in a
dedicated scientific-repository branch. Decision unlocked: review a concrete local revision.
Hypothesis: separating archived findings from corrected estimates preserves auditability while
removing unsupported claims. Budget: local CPU, literature lookup, zero experimental provider
calls. Stop: tested, compiled immutable branch plus fresh read-only diff review; no publication.

Source: `alemaiorano/sim-to-real-validity@7c1ab46b5d881529b79769fb870ed1f2fb98619c`.
Branch: `research/sim-to-real-corrections-2026-10-31`.
The marketing-simulator monorepo and its embedded paper copy are outside this change.

## Accepted proposal

[Astra high consensus](../../audit/astra-consensus.txt) accepted
[plan v3](../../audit/plan-v3.txt), SHA256
`d89e43dd74d044db8219e50efc0cd7085828a9e5d5b5a488321f00437ea43340`.
The review was consultative and read-only. It did not validate results or authorize publication.
The proposal's GPT diagnostic condition was subsequently met through offline legacy replay:
all report fields reproduced, no network, 286 absent observations left missing.
Original responses remain unavailable.

## Audit disposition

[Original findings](../../audit/original-findings.json) retain the source evidence and lines
from the pinned release; those line numbers do not describe the revised source.

| ID | Change now | Remaining limitation |
|---|---|---|
| A01 | Shared bilateral z screen, all-pairs Bonferroni, unique winner must beat every opponent | Approximate binomial assumptions; no global FDR or causal guarantee |
| A02 | Historical gamma explicitly named; actual tau-b separate throughout new summaries | Gemini corrected estimates require raw observations |
| A03 | Per-metric total/valid/undefined counts and per-metric paired intersections | Historical effective denominators unknown; rounded ties do not recover them |
| A04 | Remove unsupported package-mean power claim; retain planning artifact as historical | No new prospective power justification |
| A05 | Remove prompt-robustness outcome claim | Result artifact not recovered; not proof that no experiment occurred |
| A06 | Distinguish equal-persona H5 mean from observation-weighted primary reference | Aggregate reports do not establish cause of historical discrepancy |
| A07 | Strict finite nonboolean JSON number; no clamping/number salvage; terminal failure status; new namespace | Cannot validate old raw responses from accepted scalar values |
| A08 | Remove non-significance implies unpredictability and identified-bias mechanism claims | Mechanism and generalization require new experiments |
| A09 | Correct Reddit top-1/lift exception in abstract, text, captions and claim map | Observational design and undocumented subset selection remain |
| A10 | State GPT 30/10 budget, 399/395 historical coverage, paired count and absent seed | Retrospective reanalysis is still unequal-budget, post-parser evidence |
| A11 | Describe already completed historical aggregation comparisons | H5 code retains distinct estimands |
| A12 | Expose Reddit manifest/evaluated-subset discrepancy | Selection lineage for 600 evaluated packages not recovered |
| A13 | Distinguish report reexport from raw recomputation; supply exact GPT replay/diagnostic commands | Gemini raw and some historical report producers unavailable |
| A14 | Add primary MIND and Reddit citations; bind Park's 85% statement to v1 | No newly invented data provenance |
| G/M | Qualify preregistration, panel regeneration/representativeness, historical pilot assertions; improve schematic | No verified preregistration chronology or deterministic demographic-to-profile procedure |
| SD | Label stored stability SD as population SD over three seeds | Population vs sample convention is not itself a data error |

## Concrete outputs

- Historical reports and dataset manifests remain byte-identical to the source release.
  A closed hash-checked adapter supplies truthful gamma presentation.
- New analysis outputs are separate and exclusive; corrected builders require a new directory.
- The restored CSV rebuild preserves all 1,695 packages and 6,978 variant records. Corrected
  selection is 190, all inside the original 399; excluded packages are not thereby false winners.
- Corrected GPT coverage: panel 190, baseline 189, paired 189. Distinct gamma and tau-b, tied
  top-1/lift, valid IDs and denominator fields are in the new report.
- All displayed corrected paired-gap CIs exclude zero. This supports only that retrospective
  diagnostic on the recorded scores, not independent replication or universal persona harm.
- Revised PDF, generated tables/macros/figures, source mappings and reproduction documentation
  are committed together. New derivative provenance pins input and producer hashes.

## Validation and next decision

See [validation record](../../audit/validation.json), [reanalysis provenance](../../../reanalysis/2026-10-31/provenance.json)
and [replication commands](../../../REPLICATION.md).
A fresh Astra high PR Review approved implementation target
`a04f6582ee9ff72023618db108f6a63ccb3a073d` with no P0/P1. Its single P2 editorial note
was to label the pilot's n as total coverage and disclose unknown coefficient-specific valid
counts directly in that caption; this follow-up makes that change. The final commit receives
a bounded review of the amended caption/build and unchanged evidence boundaries.
Self-checks and the earlier plan consensus are not independent implementation QA.

No push, merge, arXiv submission, outbound email, endorsement, deployment, or paid generation
was performed. Missing Gemini raw is an explicit scientific limitation, not a reason to invent
corrected results or block the honest local revision.
