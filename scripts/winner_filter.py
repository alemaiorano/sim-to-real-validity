"""Approximate simultaneous winner screen, not a ground-truth guarantee.

Two-sided pooled-proportion z tests are Bonferroni-adjusted over all k(k-1)/2
pairs. The observed unique maximum must beat every competitor. The nominal
per-package error bound depends on each approximate test's assumptions; it
does not establish causal comparability or error rates among selected packages.
"""
import math

POLICY = "two-sided-z-all-pairs-bonferroni-v1"
ALPHA = 0.05


def evaluate_winner(variants, alpha=ALPHA):
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    counts = []
    for variant in variants:
        clicks, impressions = variant["clicks"], variant["impressions"]
        if type(clicks) is not int or type(impressions) is not int or not 0 <= clicks <= impressions or impressions <= 0:
            raise ValueError("winner screen requires integer 0 <= clicks <= impressions and positive impressions")
        rate = clicks / impressions
        if "real_ctr" in variant and not math.isclose(variant["real_ctr"], rate, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("real_ctr disagrees with the recorded counts")
        counts.append((clicks, impressions, rate))
    k = len(counts)
    result = {"selected": False, "adjusted_p": None, "policy": POLICY,
              "alpha": alpha, "n_pairs": k * (k - 1) // 2, "winner_index": None}
    if k < 2:
        return result
    winner = max(range(k), key=lambda i: counts[i][2])
    if sum(row[2] == counts[winner][2] for row in counts) != 1:
        return {**result, "adjusted_p": 1.0}
    c1, n1, p1 = counts[winner]
    pvalues = []
    for j, (c2, n2, p2) in enumerate(counts):
        if j == winner:
            continue
        pooled = (c1 + c2) / (n1 + n2)
        se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
        pvalues.append(math.erfc(abs(p1 - p2) / se / math.sqrt(2)) if se else 1.0)
    adjusted = min(1.0, result["n_pairs"] * max(pvalues))
    return {**result, "selected": adjusted < alpha, "adjusted_p": adjusted, "winner_index": winner}


def tag_package(package):
    decision = evaluate_winner(package["variants"])
    return {**package, "winner_selected": decision["selected"],
            "winner_adjusted_p": decision["adjusted_p"], "winner_filter_policy": POLICY}
