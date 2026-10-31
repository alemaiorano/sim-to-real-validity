# Explicit Azure content-filter continuation — 2026-10-31

Objective: finish only the remaining requests in the already authorized frozen research allocation,
without reissuing a blocked observation or altering content, models, seeds, sampling, or budget.
The original source is cba15e9cd676ba9c871f873e1b6ad3bc7b094996.

Observed before any efficacy inspection: Azure HTTP400/error.code=content_filter and
innererror.code=ResponsibleAIPolicyViolation halted the collector at 4,066/12,020 terminal
requests. The three requested scores are absent, not zeros. The original raw prefix is
8,139 lines, SHA256 3a37c8c53e7ebefc807f57a0df9c81868893f100af0f8dd1089b2f723255ef01,
and its mirror is identical. There are no unanswered dispatches. Recomputed liability is
USD3.664080 of the unchanged v2 USD31.998856 ceiling; no budget reset is permitted.

Astra high's read-only proposal review accepted a narrow, explicit amendment. Microsoft documents
this typed HTTP400 as a content refusal:
https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter

The continuation requires a retained, mirrored amendment document containing the original plan
hash, byte-pinned pre-amendment prefix, boundary row identity, new full source commit and code
hashes. It appends one amendment marker to the existing hash chain. Only recollect.py and its raw
replay consumer may differ from the original five pinned dependencies. Existing dispatches,
results, costs and completed IDs remain immutable. The new parser/metrics are unchanged.

Only the exact Azure400+content_filter+ResponsibleAIPolicyViolation raw type becomes terminal
missing without halting unrelated requests. No semantic retry, prompt rewriting, filter setting
change or request replacement is allowed. Other400/401/403/404 responses and understated reservations
still produce durable global stops. An amended journal cannot resume without acknowledging its
amendment. Replay validates the original prefix, marker position and amendment identity and
reports the amendment explicitly. Primary complete-package coverage is unchanged; any package
with missing observations remains excluded. Content-dependent exclusions and the temporal pause
must be disclosed as scientific limits.

Implementation uses a separate source worktree so the active Gemini collector's pinned files
remain unchanged. All 19 focal producer/replay/retention tests pass, including no blocked-request
reissue, repeated known refusal, exact cost/done restoration, one marker across resume, wrong
amendment rejection, changed scientific dependencies, and unrelated permanent stops. Provider
calls are stubbed in these tests. A frozen-source read-only review precedes live continuation.
