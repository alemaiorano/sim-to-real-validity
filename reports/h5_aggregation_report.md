# H5 — Aggregation Robustness of the Persona-Panel Result

**Question.** The primary result aggregates the persona panel with a plain arithmetic
**mean** over persona×draw observations. The paper lists "single aggregation rule" as an
untested design choice. Does a smarter rule recover the validity the panel loses against the
no-persona baseline?

**Method.** Re-analysis only — **no new API calls**. Per-persona raw scores come from the
resumable checkpoint `data/predictions/.checkpoint-gemini-3_1-flash-lite-sig3.jsonl`
(399 reliable-winner packages × 10 personas × 3 draws = 44,782 observations); ground truth
from `data/joined.csv`. Six aggregation rules evaluated with the same within-package metrics
and 10,000-iter bootstrap CIs as `compute_validity.py` (functions reused, not reimplemented).
Reproduce with `python scripts/analyze_h5_aggregation.py` → `reports/h5_aggregation.{json,csv}`.

**Results (n=399 reliable-winner packages; 95% bootstrap CI).**

| rule | Kendall τ | top-1 | lift captured |
|---|---|---|---|
| **baseline (no persona)** | **0.361 [0.289, 0.430]** | **0.492 [0.442, 0.543]** | 0.580 |
| panel mean *(published)* | 0.084 [0.020, 0.147] | 0.348 [0.301, 0.393] | 0.453 |
| **median** | **0.141 [0.076, 0.205]** | **0.393 [0.346, 0.441]** | 0.498 |
| trimmed-20% | 0.081 [0.017, 0.144] | 0.343 [0.296, 0.388] | 0.451 |
| z-mean (per-persona normalized) | 0.064 [0.001, 0.128] | 0.336 [0.291, 0.383] | 0.446 |
| Borda (rank fusion) | 0.081 [0.018, 0.146] | 0.353 [0.308, 0.401] | 0.470 |
| Condorcet / Copeland (pairwise majority) | 0.079 [0.014, 0.146] | 0.358 [0.313, 0.406] | 0.466 |

**Sanity check.** The `mean` rule reproduces the published primary number (τ=0.084, top-1≈34.8%
vs reported 34.6%) — the H5 pipeline is faithful.

**Findings.**

1. **The negative result is robust to aggregation choice.** No persona rule reaches the
   no-persona baseline; every persona CI's upper bound (max 0.205 for median) sits below the
   baseline lower bound (0.289). The gap is not an artifact of how the panel is pooled.

2. **The mean is a poor estimator — median recovers ~21% of the gap.** Median lifts τ from
   0.084 to **0.141** (+68% relative) and top-1 from 34.8% to **39.3%**, implying the panel
   mean is dragged by a skewed/heavy-tailed per-persona score distribution. Real but
   insufficient: still ~0.22 τ below baseline.

3. **Rank fusion does not help.** Borda and Condorcet — which discard score *levels* entirely
   and use only persona *orderings* — land at τ≈0.08, no better than the mean. So the failure
   is not per-persona scale/offset bias; it is **genuine mis-ordering** by the personas
   themselves, corroborating the paper's systematic-mis-ordering error analysis. z-mean
   (explicit per-persona normalization) even slightly hurts, confirming the same.

**Takeaway for the paper.** Strengthens, not overturns, the headline. Add a robustness
paragraph: "Across six aggregation rules including rank fusion (Borda) and pairwise majority
(Condorcet), no rule recovers baseline validity; median best mitigates the panel mean's
outlier sensitivity (τ 0.084→0.141) but the persona panel remains decisively below the
no-persona baseline (non-overlapping CIs)." Closes the stated aggregation-rule limitation.

**Connection to the agenda.** This is the breadth-vs-mass thesis in microcosm: persona
orderings carry *some* signal (median/CIs exclude zero) but cannot be pooled into a
calibrated *point* prediction that beats a plain population-level reader.
