# Recollection for a journal replication artifact — 2026-10-31

User authorization: assess necessity and actually rerun necessary LLM experiments, revise the
paper and preserve all artifacts. This replaces the previous task's zero-provider envelope for
this standalone research work only. Product release, custody and deployment work remain out of scope.

Base: `c252e7641eea506a7b9cb263bfe7683139ddb4a4` on the existing dedicated paper branch.

## Decision and fixed scope

New observations are necessary: the historical Gemini predictions could not be recovered.
The GPT scalar checkpoint supports offline replay but cannot validate original responses and has
unequal sampling budgets. Recollect both model families on the same frozen corrected cohort,
preserving the old data as historical evidence. Do not repeat all five datasets or select a
preferred model after seeing outcomes. Generalization to those datasets remains historical.

- Population: all 190 packages/601 variants passing the corrected screen in the exact original
  exploratory corpus. Preserve the complete original corpus and CSV plus selected IDs.
- Models: Gemini `gemini-3.1-flash-lite` and the existing Azure `gpt-4.1` deployment. The metadata
  endpoints returned HTTP 200 before generation. Record returned versions on every response.
- Each variant: 10 personas × 3 observations, compared with 30 generic-reader observations.
  Each model therefore plans 36,060 observations; total 72,120.
- Azure's observed quota is 150 requests/minute. Protocol v2 uses n=3 symmetrically:
  ten requests per arm/variant, three choices each, 12,020 Azure requests total. Interleave
  requests, assign unique request/choice indices and require exactly indices 0–2. Do not
  assume the choices are independent or this request protocol is operationally identical
  to Gemini's single-choice requests. Usage is charged once per request; reserve output
  for all three choices. Each Azure request has one seed, not an invented seed per choice.
- Temperature 0.8, JSON mode, strict finite nonboolean parser. Gemini uses documented MINIMAL
  thinking; Azure GPT-4.1 has no reasoning budget. This is a new protocol, not historical replay.
- Fixed seeded package/variant order, randomized order within each baseline/panel pair,
  contemporaneous interleaving, shared pair seed 42+pair index when supported. In Azure v2
  the pair index is the ten-request group index; Gemini retains thirty sample pairs.
- No outcome-dependent stopping or model/prompt selection. Technical compatibility probes are
  retained separately if configuration changes are needed. Semantic failures are terminal.
- Primary comparison requires the complete planned per-persona and baseline observations for
  every variant in a package in both arms. Retain all failures and report exclusions. Separately
  describe available-observation sensitivity without confusing its weighting with complete data.
- Reuse gamma, tau-b, Spearman, expected tie credit, lift and paired bootstrap owners already
  reviewed. Primary inference is conditional on selected packages and this collection session.
  The cohort was defined from historical data; this is not a newly held-out population.

## Budget and retention

Operational liability caps: Gemini USD8, Azure USD32, total USD40. Conservative accounting must
reserve cost before each attempt, count unknown-use attempts without treating them as free,
bound total attempts and retries, and stop on permanent configuration/authentication errors.
Pricing reference: Gemini 0.25/1.50 per million input/output tokens; Azure GPT-4.1 reference
pricing and its deployment-dependent limits are recorded with the run. Runtime accounting is
an estimate rather than an invoice. No automated provider fallback or budget reset.

Before dispatch, durably save the request, observation key and reservation. Save every raw
response or failure, token usage, response ID, version, seed, timestamps and HTTP status.
Keep append-only journals, configuration/input/source hashes, exact sampling plan, parser output,
per-variant aggregates, package metrics, code and reproduction commands. Resume from retained
events; never silently recollect completed observations or discard a failed attempt.
Honor known RPM, reported TPM and retry-after including milliseconds; a permanent HTTP error
or underestimated reservation remains halted after restart. Analyze and hash the same retained
snapshot; never attribute a report to a later, concurrently appended journal.

Four compatibility observations from source d70581d7a19042170042198d9eb6780b05927335
were HTTP200/valid (two per model), but are retained separately as protocol-v1 diagnostics.
Their conservative liabilities (Gemini0.0001830/Azure0.001144USD) are deducted from v2's caps.
They are not pooled into v2 scientific results. Review found and repaired durable-stop,
snapshot identity and pacing defects before any full collection. Counterexamples are retained
as producer/replay tests. No API calls were made by the read-only reviewer.

Canonical sink: `/home/maioale/eval-artifacts/marketing-simulator/paper-recollection/2026-10-31/`.
Keep a second durable copy outside worktrees under `/home/maioale/research-backups/`, then make
a checksummed archive copy on the Windows volume. Secrets are never copied into those artifacts.
The bundle must include the original GPT scalar checkpoint, its hash and historical replay
evidence alongside the new observations. Original `reports/` and locks remain immutable.

## Required result

Test the collector's retention, resume, interleaving, budget and raw-replay behavior with stubbed
transports; freeze its source before paid collection. Complete the declared cohort when supported
by credentials/quota/budget. Recompute from saved responses independently of API calls, regenerate
paper assets, audit claims against observed outcomes and package the artifact. Preserve and report
partial evidence if an external limit prevents completion. No journal submission or remote
publication is authorized by this task.

## Integration and portability

The correction manuscript now distinguishes historical report verification, scalar-checkpoint
reanalysis, and the new raw-retained experiment. The new report/table exporter rejects unfinished
observations or mismatched report/plan hashes. Reviewer exports preserve observation IDs and
request/choice/response hashes, variant means with missingness, and package metrics including
undefined fields. Their source is the exact immutable journal snapshot checked by offline replay.
The exporter is separate from frozen collection dependencies and does not affect running calls.

Retain environment versions and exact input hashes, not credentials. The final archive uses a
file manifest and SHA256SUMS, includes both collector and final-source Git bundles, and must be
verified after copying to Linux backup and the Windows volume. The Windows destination is outside
OneDrive. Future remote deposition and journal submission remain author actions.

Exporter validation: a real stubbed Azure producer returns heterogeneous choices out of order;
CSV export must keep choice lineage and empty undefined rank coefficients, refuse changed reports
and existing output directories. All 17 focal collection/retention/export tests pass. No live
provider calls are part of the tests.

## Completed result

All 72,120 planned observations reached terminal outcomes: 72,058 valid and 62 missing.
Gemini completed 36,060 requests plus two transport retries; two numeric-string outputs remained
invalid. Azure completed 12,020 three-choice requests plus ten transport retries; twenty content
refusals left sixty scores absent. Each model retained 188 complete primary packages, with
different excluded IDs. No semantic draw was replaced. V2 and retained V1 probes account for
USD14.2565545 at conservative rates, not provider invoices.

The baseline has positive paired gaps for valid rank metrics, expected top-1 and lift in both
configurations. Bottom-1 intervals include zero. Gemini rank counts are 185 panel, 137 baseline
and 136 paired: 51 baseline and three panel packages are undefined, with two overlapping.
Constant predictions are not imputed zero. Top-1 uses all 188 complete packages with expected tie
credit. Marginal rank mean differences are not substituted for paired estimates.

Analysis/export code was frozen at 3e1e32b before comparative analysis. Reports are byte-identical
when replayed in an offline clone restored from its Git bundle. A SciPy/direct-definition oracle
checked 6,816 package-metric cells, all 72,120 observation rows and 2,404 variant-arm rows. Means,
undefined values, valid IDs and denominators match. New tables/prose read hash-pinned reports.
All 24 references resolve, every float is discussed, 19 historical artifacts remain byte-identical,
and the 12-page PDF has no warnings or overfull boxes and a deterministic rebuild.
See docs/audit/recollection-validation.json for reproducible checks and source/artifact pins.
