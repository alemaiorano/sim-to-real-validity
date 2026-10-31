#!/usr/bin/env python3
"""Adapt the SNAP Reddit submissions dataset (Lakkaraju et al., ICWSM 2013, "What's in a name?")
into the sim-to-real corpus schema: a fifth observational benchmark on a different platform/era.

Design: the SAME image resubmitted with DIFFERENT titles holds the image constant but does not isolate a causal title effect. We group by (image_id, subreddit), treat each distinct title as a variant,
use the upvote ratio up/(up+down) as the real outcome, total votes as n, and the shared two-sided all-pairs Bonferroni screen. Votes are an observational proxy;
independent-binomial assumptions need not hold.
Caveat: resubmission timing/visibility confounds raw score; using the RATIO and grouping by
subreddit does not eliminate these confounders.

Output: datasets/reddit-subset-<DATE>.json (same schema). Fails loudly if input absent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from winner_filter import evaluate_winner, POLICY
from analysis_io import write_json

SEED = 42
LOCK_DATE = "2026-10-31"
MIN_VOTES = 300            # per-variant total votes for ratio reliability
MIN_VARIANTS = 2
MAX_VARIANTS_PER_PKG = 10
PAPER_DIR = Path(__file__).resolve().parents[1]
RAW = PAPER_DIR / "data" / "reddit_raw" / "redditSubmissions.csv"
OUT = PAPER_DIR / "datasets" / f"reddit-subset-{LOCK_DATE}.json"


def fail(m): print(f"[reddit][FATAL] {m}", file=sys.stderr); sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--output-dir", type=Path, required=True, help="new corpus directory; historical locks are never overwritten")
    args = ap.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    if not RAW.exists():
        fail(f"missing {RAW} (download snap.stanford.edu/data/redditSubmissions.csv.gz)")
    raw = RAW.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()

    grp = defaultdict(dict)  # (image,subreddit) -> title -> [up, down]
    reader = csv.DictReader(raw.decode("utf-8", "replace").splitlines())
    for r in reader:
        try:
            up = int(r["number_of_upvotes"]); dn = int(r["number_of_downvotes"])
        except (ValueError, KeyError, TypeError):
            continue
        title = (r.get("title") or "").strip()
        if not title:
            continue
        cell = grp[(r["#image_id"], r["subreddit"])].setdefault(title, [0, 0])
        cell[0] += up; cell[1] += dn

    corpus = []
    for (img, sub), titles in grp.items():
        vs = []
        for t, (u, d) in titles.items():
            n = u + d
            if n >= MIN_VOTES:
                vs.append({"variant_id": hashlib.md5(f"{img}|{sub}|{t}".encode()).hexdigest()[:10],
                           "headline": t, "impressions": n, "clicks": u, "real_ctr": u / n})
        vs = sorted(vs, key=lambda v: -v["impressions"])[:MAX_VARIANTS_PER_PKG]
        if len(vs) < MIN_VARIANTS:
            continue
        decision = evaluate_winner(vs)
        corpus.append({"package_id": f"{img}:{sub}", "subreddit": sub, "variants": vs,
                       "winner_selected": decision["selected"], "winner_adjusted_p": decision["adjusted_p"],
                       "winner_filter_policy": POLICY})

    n_sig = sum(1 for c in corpus if c["winner_selected"])
    print(f"[reddit] {len(corpus)} packages (image x subreddit, >= {MIN_VARIANTS} distinct titles, "
          f">= {MIN_VOTES} votes), {n_sig} significant-winner, "
          f"{sum(len(c['variants']) for c in corpus)} variants")
    if args.dry_run:
        return
    args.output_dir.mkdir(parents=True, exist_ok=False)
    output = args.output_dir / OUT.name
    write_json(output, corpus)
    write_json(output.with_suffix(".manifest.json"), {
        "source": "SNAP Reddit submissions (Lakkaraju et al., ICWSM 2013)",
        "source_sha256": src_sha, "lock_date": LOCK_DATE, "min_votes": MIN_VOTES,
        "outcome": "upvote ratio up/(up+down); approximate simultaneous z screen",
        "grouping": "image_id x subreddit (content+community held constant; title varies)",
        "n_packages": len(corpus), "n_packages_selected": n_sig, "winner_filter_policy": POLICY,
        "n_variants": sum(len(c["variants"]) for c in corpus),
        "corpus_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    })
    print(f"[reddit] wrote {output}")


if __name__ == "__main__":
    main()
