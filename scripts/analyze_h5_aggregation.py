#!/usr/bin/env python3
"""Compare aggregation rules on explicitly supplied recorded observations, without provider calls.
The historical mean weights collapsed personas equally; mean_observation separately mirrors the
primary collector. Only corrected-policy joined inputs and new output destinations are accepted.
Historical raw parsing cannot be validated from these scalar scores.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from analysis_io import write_json
from winner_filter import POLICY
from importlib import import_module

load_predictions = import_module("03_build_joined").load_predictions

PAPER_DIR = Path(__file__).resolve().parents[1]
JOINED = PAPER_DIR / "data" / "joined.csv"
PRED = PAPER_DIR / "data" / "predictions"
CKPT = PRED / ".checkpoint-gemini-3_1-flash-lite-sig3.jsonl"
BASELINE = PRED / "gemini-3_1-flash-lite-baseline.jsonl"
REPORTS = PAPER_DIR / "reports"

spec = importlib.util.spec_from_file_location("cv", PAPER_DIR / "scripts" / "compute_validity.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)  # canonical ranking estimators


def fail(msg: str) -> None:
    print(f"[h5][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def load_ground_truth(path):
    gt = defaultdict(dict)
    for row in csv.DictReader(Path(path).open()):
        if row.get("winner_filter_policy") != POLICY:
            raise ValueError("joined input must carry corrected selection policy")
        if row["winner_selected"] == "1":
            gt[row["package_id"]][row["variant_id"]] = float(row["real_ctr"])
    return {k: v for k, v in gt.items() if len(v) >= 2}


def load_observations(path):
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    seen = set()
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["package_id"], row["variant_id"], row["persona_id"], row["draw"])
        if key in seen:
            raise ValueError("duplicate per-persona observation")
        seen.add(key)
        if row.get("status") == "invalid_or_unavailable" and row["value"] is None:
            continue
        value = row["value"]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("invalid per-persona score")
        raw[key[0]][key[1]][key[2]].append(value)
    return raw


def collapse_personas(observations):
    return {pkg: {var: {persona: sum(scores) / len(scores) for persona, scores in people.items()}
                  for var, people in variants.items()} for pkg, variants in observations.items()}


def mean_observation(variants):
    return {var: sum(score for scores in people.values() for score in scores) /
                 sum(len(scores) for scores in people.values()) for var, people in variants.items()}


def load_baseline_pred(path) -> dict[str, dict[str, float]]:
    """no-persona baseline final preds -> {package: {variant: pred_score}}."""
    out = defaultdict(dict)
    for (pid, vid), value in load_predictions(path).items():
        out[pid][vid] = value
    return out


# ---- aggregation rules: dict[persona -> score] over variants of one package -> dict[variant -> score]

def _trimmed_mean(xs: list[float], frac: float = 0.1) -> float:
    xs = sorted(xs)
    k = int(len(xs) * frac)
    core = xs[k: len(xs) - k] or xs
    return sum(core) / len(core)


def agg_level(per_persona: dict[str, dict[str, float]], how: str) -> dict[str, float]:
    """Level-based rules: pool persona scores per variant, then reduce."""
    out = {}
    for var, pmap in per_persona.items():
        vals = list(pmap.values())
        if how == "mean":
            out[var] = sum(vals) / len(vals)
        elif how == "median":
            out[var] = statistics.median(vals)
        elif how == "trimmed20":
            out[var] = _trimmed_mean(vals, 0.1)
        else:
            raise ValueError(how)
    return out


def agg_zmean(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """z-score each persona ACROSS the package's variants, then mean across personas.
    Removes per-persona scale/offset (a persona who rates everything high adds no signal)."""
    variants = list(per_persona.keys())
    # rebuild as persona -> {variant: score}
    by_persona: dict[str, dict[str, float]] = defaultdict(dict)
    for var, pmap in per_persona.items():
        for persona, s in pmap.items():
            by_persona[persona][var] = s
    contrib: dict[str, list[float]] = defaultdict(list)
    for persona, vmap in by_persona.items():
        if len(vmap) < len(variants):  # persona must score every variant to contribute
            continue
        vals = list(vmap.values())
        mu = sum(vals) / len(vals)
        sd = statistics.pstdev(vals)
        for var, s in vmap.items():
            contrib[var].append((s - mu) / sd if sd > 0 else 0.0)
    if not contrib:
        return {}
    return {var: (sum(cs) / len(cs) if cs else None) for var, cs in
            ((v, contrib.get(v, [])) for v in variants)}


def _persona_ballots(per_persona: dict[str, dict[str, float]]) -> tuple[list[str], list[dict[str, float]]]:
    """variants + list of per-persona {variant: score}, keeping only personas that scored all."""
    variants = list(per_persona.keys())
    by_persona: dict[str, dict[str, float]] = defaultdict(dict)
    for var, pmap in per_persona.items():
        for persona, s in pmap.items():
            by_persona[persona][var] = s
    ballots = [vmap for vmap in by_persona.values() if len(vmap) == len(variants)]
    return variants, ballots


def agg_borda(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """Rank fusion: each persona ranks variants; Borda points summed (ties share avg points)."""
    variants, ballots = _persona_ballots(per_persona)
    if not ballots:
        return {}
    score = {v: 0.0 for v in variants}
    for vmap in ballots:
        ranks = cv._ranks([vmap[v] for v in variants])  # 1=lowest score
        for v, rk in zip(variants, ranks):
            score[v] += rk  # higher rank (higher score) -> more Borda points
    return score


def agg_condorcet(per_persona: dict[str, dict[str, float]]) -> dict[str, float]:
    """Copeland: for each ordered pair, count personas preferring it; variant score = #pairwise wins."""
    variants, ballots = _persona_ballots(per_persona)
    if not ballots:
        return {}
    wins = {v: 0.0 for v in variants}
    for i in range(len(variants)):
        for j in range(i + 1, len(variants)):
            a, b = variants[i], variants[j]
            pa = sum(1 for vm in ballots if vm[a] > vm[b])
            pb = sum(1 for vm in ballots if vm[b] > vm[a])
            if pa > pb:
                wins[a] += 1
            elif pb > pa:
                wins[b] += 1
            else:
                wins[a] += 0.5
                wins[b] += 0.5
    return wins


RULES = {
    "mean": lambda pp: agg_level(pp, "mean"),
    "median": lambda pp: agg_level(pp, "median"),
    "trimmed20": lambda pp: agg_level(pp, "trimmed20"),
    "zmean": agg_zmean,
    "borda": agg_borda,
    "condorcet": agg_condorcet,
}


def evaluate(gt, pred_by_pkg, iters=cv.BOOTSTRAP_ITERS):
    packages = {}
    for pkg, real_map in gt.items():
        pred = pred_by_pkg.get(pkg, {})
        if not all(v in pred and pred[v] is not None for v in real_map):
            continue
        packages[pkg] = [(real_map[v], pred[v]) for v in real_map]
    return {"n_eligible": len(gt), "n_missing_prediction_coverage": len(gt) - len(packages),
            **cv.analyze(packages, iters)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--joined", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    gt = load_ground_truth(args.joined)
    raw = load_observations(args.checkpoint)
    per_persona = collapse_personas(raw)
    results = {"baseline_no_persona": evaluate(gt, load_baseline_pred(args.baseline)),
               "mean_observation": evaluate(gt, {pkg: mean_observation(vs) for pkg, vs in raw.items()})}
    for name, aggregate in RULES.items():
        results[name] = evaluate(gt, {pkg: aggregate(vs) for pkg, vs in per_persona.items()})
    write_json(args.output, {"analysis_schema": cv.METRIC_POLICY, "winner_filter_policy": POLICY,
                            "mean_identity": "equal_persona_weight_after_draw_collapse",
                            "mean_observation_identity": "equal_recorded_observation_weight",
                            "results": results})


if __name__ == "__main__":
    main()
