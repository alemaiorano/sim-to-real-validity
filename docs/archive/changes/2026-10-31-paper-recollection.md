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
- Temperature 0.8, JSON mode, strict finite nonboolean parser. Gemini uses documented MINIMAL
  thinking; Azure GPT-4.1 has no reasoning budget. This is a new protocol, not historical replay.
- Fixed seeded package/variant order, randomized order within each baseline/panel pair,
  contemporaneous interleaving, shared pair seed 42+pair index when supported.
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
