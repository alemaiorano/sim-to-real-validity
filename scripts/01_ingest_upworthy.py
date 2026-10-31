#!/usr/bin/env python3
"""Build a locked exploratory subset of the Upworthy Research Archive
~\\cite{matiasUpworthy} as the sim-to-real ground-truth corpus.

Source: Upworthy Research Archive, Matias et al., Scientific Data 8, 195 (2021).
  DOI:  10.1038/s41597-021-00934-7
  OSF:  https://osf.io/jd64p/   (download the exploratory packages CSV from there)

We do NOT re-host the Upworthy data. This script reads a locally-downloaded CSV,
records its sha256, deterministically constructs an exploratory subset, and writes a
locked corpus JSON whose every variant carries the REAL click-through rate.

The archival exploratory split and a deterministic construction do not establish that this
revision is held out, that thresholds were preregistered, or that model contamination is absent.
The preserved source lacks the archive's 2024 randomization-risk flags; the paper reports that
limitation and a separate period-exclusion sensitivity, not a silent change to historical locks.

Output: datasets/upworthy-subset-<LOCK_DATE>.json   (corpus)
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
from winner_filter import evaluate_winner, POLICY
from analysis_io import write_json

# Deterministic sampling parameters — changing any of these changes the corpus id.
SEED = 42
# Packages must have at least this many variants for a ranking task to be meaningful.
MIN_VARIANTS_PER_PACKAGE = 2
# Minimum total impressions per variant for the observed CTR to be trustworthy.
# Raised for ground-truth reliability (CTR standard error ~ sqrt(p(1-p)/n)); this filters on
# the GROUND-TRUTH side only, never on effect size, so it changes the conditional evaluation population.
MIN_IMPRESSIONS = 3000
# Zero means all eligible packages. This is not a power justification for a package-mean coefficient.
SAMPLE_PACKAGES = 0
LOCK_DATE = "2026-10-31"

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


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest Upworthy archive into a locked exploratory corpus.")
    ap.add_argument("--input", required=True, type=Path, help="path to an Upworthy packages CSV")
    ap.add_argument("--name", default="upworthy-subset",
                    help="output corpus base name (use a distinct name per split to avoid clobber)")
    ap.add_argument("--output-dir", type=Path, required=True, help="new corpus directory; historical locks are never overwritten")
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)

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
        decision = evaluate_winner(packages[pid])
        corpus.append({
            "package_id": pid,
            "variants": packages[pid],
            "winner_selected": decision["selected"],
            "winner_adjusted_p": decision["adjusted_p"],
            "winner_filter_policy": POLICY,
        })
    n_sig = sum(1 for c in corpus if c["winner_selected"])

    args.output_dir.mkdir(parents=True, exist_ok=False)
    out = args.output_dir / f"{args.name}-{LOCK_DATE}.json"
    write_json(out, corpus)

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
        "n_packages_selected": n_sig,
        "n_variants": sum(len(p["variants"]) for p in corpus),
        "winner_filter_policy": POLICY,
        "winner_alpha_per_package": 0.05,
        "calibration": "approximate, conditional on the pooled-proportion z-test assumptions",
        "corpus_file": out.name,
        "corpus_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    write_json(out.with_suffix(".manifest.json"), manifest)
    print(f"[upworthy] wrote {out} ({manifest['n_packages']} packages, "
          f"{manifest['n_variants']} variants)")
    print(f"[upworthy] manifest sha256 {manifest['corpus_sha256']}")


if __name__ == "__main__":
    main()
