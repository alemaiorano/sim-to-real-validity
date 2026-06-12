#!/usr/bin/env python3
"""Build a locked, held-out subset of the Upworthy Research Archive
~\\cite{matiasUpworthy} as the sim-to-real ground-truth corpus.

Source: Upworthy Research Archive, Matias et al., Scientific Data 8, 195 (2021).
  DOI:  10.1038/s41597-021-00934-7
  OSF:  https://osf.io/jd64p/   (download the exploratory packages CSV from there)

We do NOT re-host the Upworthy data. This script reads a locally-downloaded CSV,
records its sha256, deterministically samples a held-out subset, and writes a
locked corpus JSON whose every variant carries the REAL click-through rate.

The subset is HELD-OUT: it is never shown to the persona-authoring step, so any
predictive signal measured later is generalization evidence, not self-reference.

Output: research/datasets/upworthy-subset-<LOCK_DATE>.json   (corpus)
        sibling .manifest.json                               (sha256 + sampling params)

Hard rule: this script FAILS LOUDLY if the input is absent or its schema is
unexpected. It never synthesizes placeholder rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from pathlib import Path

# Deterministic sampling parameters — changing any of these changes the corpus id.
SEED = 42
# Packages must have at least this many variants for a ranking task to be meaningful.
MIN_VARIANTS_PER_PACKAGE = 2
# Minimum total impressions per variant for the observed CTR to be trustworthy.
# Raised for ground-truth reliability (CTR standard error ~ sqrt(p(1-p)/n)); this filters on
# the GROUND-TRUTH side only, never on effect size, so it does not bias the validity estimate.
MIN_IMPRESSIONS = 3000
# Number of packages to sample. 0 = use ALL eligible packages (no arbitrary cap). Sized for
# statistical power (power_analysis.py): with the package as the inferential unit, the full
# eligible pool yields ~399 significant-winner packages, which powers the primary rank-
# correlation claim at Cohen-small-to-medium effects (rho>=0.15 needs n=347). See POWER_ANALYSIS.md.
SAMPLE_PACKAGES = 0
LOCK_DATE = "2026-06-03"

# Columns we rely on in the Upworthy exploratory CSV. If the source renames these,
# we fail loudly rather than guess. The variant identity for a COPY task is the distinct
# headline text (not the row id): rows within a package that share a headline differ only by
# image (eyecatcher), which a text-only persona simulator cannot distinguish. We therefore
# aggregate impressions/clicks per distinct headline within each package.
COL_PACKAGE = "clickability_test_id"
COL_HEADLINE = "headline"
COL_IMPRESSIONS = "impressions"
COL_CLICKS = "clicks"

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = REPO_ROOT / "datasets"


def fail(msg: str) -> "None":
    print(f"[upworthy][FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def load_rows(csv_path: Path) -> tuple[list[dict], str]:
    if not csv_path.exists():
        fail(
            f"input not found: {csv_path}\n"
            f"  Download the Upworthy exploratory packages CSV from https://osf.io/jd64p/\n"
            f"  and pass it with --input <path>. We do not re-host the data."
        )
    raw = csv_path.read_bytes()
    src_sha256 = hashlib.sha256(raw).hexdigest()
    reader = csv.DictReader(raw.decode("utf-8").splitlines())
    missing = [c for c in (COL_PACKAGE, COL_HEADLINE, COL_IMPRESSIONS, COL_CLICKS)
               if c not in (reader.fieldnames or [])]
    if missing:
        fail(f"input CSV missing expected columns {missing}; found {reader.fieldnames}")
    return list(reader), src_sha256


def build_packages(rows: list[dict]) -> dict[str, list[dict]]:
    # Aggregate impressions/clicks per (package, distinct headline). A headline that appears
    # across multiple image variants is pooled into a single copy-variant.
    agg: dict[str, dict[str, dict[str, int]]] = {}
    for r in rows:
        try:
            impressions = int(r[COL_IMPRESSIONS])
            clicks = int(r[COL_CLICKS])
        except (ValueError, KeyError):
            continue
        headline = r[COL_HEADLINE].strip()
        if not headline:
            continue
        pkg = agg.setdefault(r[COL_PACKAGE].strip(), {})
        cell = pkg.setdefault(headline, {"impressions": 0, "clicks": 0})
        cell["impressions"] += impressions
        cell["clicks"] += clicks

    packages: dict[str, list[dict]] = {}
    for pid, headlines in agg.items():
        variants = []
        for idx, headline in enumerate(sorted(headlines)):  # sorted → deterministic variant_id
            imp = headlines[headline]["impressions"]
            clk = headlines[headline]["clicks"]
            if imp < MIN_IMPRESSIONS:
                continue
            variants.append({
                "variant_id": f"{pid}#{idx}",
                "headline": headline,
                "impressions": imp,
                "clicks": clk,
                "real_ctr": clk / imp if imp else 0.0,
            })
        if len(variants) >= MIN_VARIANTS_PER_PACKAGE:
            packages[pid] = variants
    return packages


def _two_prop_p_one_sided(c1: int, n1: int, c2: int, n2: int) -> float:
    """One-sided p-value that variant 1's CTR exceeds variant 2's (two-proportion z-test)."""
    p1, p2 = c1 / n1, c2 / n2
    p = (c1 + c2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def tag_winner_significance(variants: list[dict]) -> tuple[bool, float]:
    """Is the top-CTR variant a statistically significant winner over the runner-up?
    This gates GROUND-TRUTH RELIABILITY (you cannot validate a predictor against a label that
    is itself noise) — justified by kohavi2009controlled. It filters on significance, NOT on
    effect-size direction, so it does not bias the validity estimate (no outcome cherry-picking).
    """
    ordered = sorted(variants, key=lambda v: -v["real_ctr"])
    top, second = ordered[0], ordered[1]
    p = _two_prop_p_one_sided(top["clicks"], top["impressions"], second["clicks"], second["impressions"])
    return (p < 0.05, p)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest Upworthy archive into a locked held-out corpus.")
    ap.add_argument("--input", required=True, type=Path, help="path to an Upworthy packages CSV")
    ap.add_argument("--name", default="upworthy-subset",
                    help="output corpus base name (use a distinct name per split to avoid clobber)")
    args = ap.parse_args()

    rows, src_sha256 = load_rows(args.input)
    print(f"[upworthy] read {len(rows)} rows; source sha256 {src_sha256}")

    packages = build_packages(rows)
    print(f"[upworthy] {len(packages)} packages pass filters "
          f"(>= {MIN_VARIANTS_PER_PACKAGE} variants, >= {MIN_IMPRESSIONS} impressions)")
    if 0 < SAMPLE_PACKAGES < len(packages):
        rnd = random.Random(SEED)
        chosen_ids = sorted(rnd.sample(sorted(packages.keys()), SAMPLE_PACKAGES))
    else:
        chosen_ids = sorted(packages.keys())   # use ALL eligible packages
    corpus = []
    for pid in chosen_ids:
        sig, p = tag_winner_significance(packages[pid])
        corpus.append({
            "package_id": pid,
            "variants": packages[pid],
            "winner_significant": sig,   # primary analysis = significant-winner packages
            "winner_p_one_sided": round(p, 5),
        })
    n_sig = sum(1 for c in corpus if c["winner_significant"])

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    out = DATASETS_DIR / f"{args.name}-{LOCK_DATE}.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    manifest = {
        "source": "Upworthy Research Archive (Matias et al., Scientific Data 2021)",
        "source_doi": "10.1038/s41597-021-00934-7",
        "source_sha256": src_sha256,
        "lock_date": LOCK_DATE,
        "seed": SEED,
        "min_variants_per_package": MIN_VARIANTS_PER_PACKAGE,
        "min_impressions": MIN_IMPRESSIONS,
        "sample_packages": SAMPLE_PACKAGES,
        "n_packages": len(corpus),
        "n_packages_significant_winner": n_sig,
        "n_variants": sum(len(p["variants"]) for p in corpus),
        "winner_significance_test": "two-proportion z-test, top vs runner-up, one-sided p<0.05 (kohavi2009controlled)",
        "corpus_file": out.name,
        "corpus_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    (out.with_suffix(".manifest.json")).write_text(json.dumps(manifest, indent=2))
    print(f"[upworthy] wrote {out} ({manifest['n_packages']} packages, "
          f"{manifest['n_variants']} variants)")
    print(f"[upworthy] manifest sha256 {manifest['corpus_sha256']}")


if __name__ == "__main__":
    main()
