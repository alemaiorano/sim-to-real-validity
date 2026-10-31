# DoesItStand: frozen manuscript and adjudication

This record concerns source `d0af68fbfbe0655b8c1ecbdc4ea9dd1da6d557e9` and PDF SHA256
`5a765385cdafd3c5bbc34f1ad22755ad3c83578dff5f76861e93f6445dabd519`.
Tool source is `b3e35a36218697fe32cc0bb82c5d8165e9b924d3`; native prompt version `v3`
identifies the review prompts, not a version label for the paper. Previous review records
remain tied to their own targets. The native output is preserved without editing.

## Scientific scope of the review

The meta-review recommends Accept, overall 7/10, confidence 4/5. This is an automated advisory
assessment, not journal acceptance, an independent human gate, or proof that all claims are true.
A score change from earlier runs is not evidence that editorial reframing improved scientific
validity. No repeated run was commissioned to seek a favorable score.

The model correctly identifies omitted generation uncertainty as a limitation. Sections 5--7
and the abstract already state that the package bootstrap conditions on the selected cohort
and recorded generations and omits repeated-generation, selection and outcome uncertainty.
The primary confidence intervals estimate that conditional package contrast. They do not claim
to estimate a total uncertainty distribution over future API runs. Resampling API requests would
be a different uncertainty analysis; it does not automatically replace package-level resampling
for the reported conditional estimand. Azure choices are not assumed independent, and both arms
within that model use the same request allocation. No inference of causal model-family effects
or equal compute, tokens, cost, or cross-provider transport is made. More independent sessions
and transport ablations are valid extensions, not missing data to invent in this manuscript.
The review's phrase "preventing statistical power artifacts" is stronger than the paper's claim:
matching score count controls that allocation only and cannot eliminate every source of bias.

Supplementary benchmark IDs, draw counts and missing response texts remain genuine limits.
The paper separates their protocols from the primary comparisons, explicitly states unknown
fields and does not reconstruct them from memory. The public scope table and per-result captions
explain aggregate reexport versus checkpoint analysis versus raw replay. A unified table cannot
supply absent lineage. Complete primary IDs, plan, raw failures and per-metric denominators are
retained in the companion; public deposition remains pending and is disclosed in the paper.

The review's parameter-omission statement is partly a missed-source issue. Section 5 provides
temperature 0.8, output cap 64, Gemini MINIMAL thinking, score allocation and Azure n=3. The
appendix explains request-level seeds, exact template ownership and fixed-2014 framing.
REPLICATION.md documents omitted top-p/penalties rather than inventing numeric provider defaults.
Exact requested/returned identities and literal prompts are retained in the source and raw
companion. The runs used aliases; an unavailable immutable snapshot ID must not be invented.
Prompt variants implemented in source are not all claimed to have completed scientific runs.

## Native integrity signals and their boundaries

The encoding guard's raw failed status is retained: six high flags are the TikZ options
`>=Stealth` and five `\\draw[->]` commands in `latex/figures/protocol.tex`. These produce arrows;
they are not body-text glyphs. Labels, images and build logs have no other guard findings.
The compiled PDF was inspected, the literal JSON placeholder extracts correctly, and a clean
clone and source-only archive rebuild the exact same PDF. Valid TikZ was not altered to silence
a text-mode heuristic, and no failed record was converted into a pass.

The claim checker reports three supported paraphrases and one unsupported paraphrase about
Upworthy randomization issues. Its implementation passes only extracted title/summary/keywords
and a short grounding sample, not the manuscript tables or its actual cited evidence. The paper
cites the archive authors' 2024 report (DOI `10.1038/s41597-024-03600-w`) and reports the precise
post-hoc exclusion results in Table 3. These data are absent from that judge's summary context.
The unsupported paraphrase is preserved; it neither refutes the primary source nor demonstrates
a numerical mismatch. Conversely, the three supported paraphrases are not substitutes for the
actual claim-to-artifact ledger. No formal heterogeneity interaction is inferred from whether
an interval crosses zero.

The resolver finds 23 of 25 references with no author mismatches. The two unresolved web sources
are Pew's *News Use Across Social Media Platforms* and NIST's Bonferroni method, already verified
against their primary pages in the unchanged bibliography audit:

- https://www.pewresearch.org/journalism/2013/11/14/news-use-across-social-media-platforms/
- https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm

The LOLA `possibly_fused` flag combines an unversioned arXiv identifier and version 3 of the same
work; it is not evidence of a fabricated merged citation. The native hallucination report has
zero potential hallucinations and zero author mismatches. No bibliography metadata was altered
to accommodate these heuristics.

## Implementation disposition

No new formula or numerical inconsistency was demonstrated. Table cells, numerical macros,
scientific inputs/reports and statistical owners remain identical to the tested base. The
editorial change organizes primary and supplementary evidence within one paper and preserves
all differing protocols and uncertainty limitations. The full native reports, SDK request and
response journals, source pins, output-cap adapter and usage accounting remain in a new retained
companion. The adapter caps the tool's excessive output-token request to the authenticated
65536-token model limit; it does not change models, prompts or scores and is SDK-object retention,
not an HTTP wire-byte capture. No scientific observations were regenerated.
