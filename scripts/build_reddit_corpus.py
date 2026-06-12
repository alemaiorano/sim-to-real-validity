#!/usr/bin/env python3
"""Adapt the SNAP Reddit submissions dataset (Lakkaraju et al., ICWSM 2013, "What's in a name?")
into the sim-to-real corpus schema: a 5th, copy-isolating benchmark on a different platform/era.

Design: the SAME image resubmitted with DIFFERENT titles isolates the copy (title) effect with
content held constant. We group by (image_id, subreddit), treat each distinct title as a variant,
use the upvote ratio up/(up+down) as the real outcome, total votes as n, and a one-sided
two-proportion z-test (top vs runner-up) for the reliable-winner filter (same as Upworthy).
Caveat: resubmission timing/visibility confounds raw score; using the RATIO and grouping by
subreddit mitigates this, and the source paper studies exactly the title effect given content.

Output: research/datasets/reddit-subset-<DATE>.json (same schema). Fails loudly if input absent.
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

SEED = 42
LOCK_DATE = "2026-06-04"
MIN_VOTES = 300            # per-variant total votes for ratio reliability
MIN_VARIANTS = 2
MAX_VARIANTS_PER_PKG = 10
PAPER_DIR = Path(__file__).resolve().parents[1]
RAW = PAPER_DIR / "data" / "reddit_raw" / "redditSubmissions.csv"
OUT = PAPER_DIR / "datasets" / f"reddit-subset-{LOCK_DATE}.json"


def fail(m): print(f"[reddit][FATAL] {m}", file=sys.stderr); sys.exit(1)


def p_one(c1, n1, c2, n2):
    if n1 == 0 or n2 == 0:
        return 1.0
    p = (c1 + c2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1/n1 + 1/n2))
    return 1.0 if se == 0 else 0.5 * (1 - math.erf(((c1/n1 - c2/n2)/se) / math.sqrt(2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
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
        ordered = sorted(vs, key=lambda v: -v["real_ctr"])
        pp = p_one(ordered[0]["clicks"], ordered[0]["impressions"],
                   ordered[1]["clicks"], ordered[1]["impressions"])
        corpus.append({"package_id": f"{img}:{sub}", "subreddit": sub, "variants": vs,
                       "winner_significant": pp < 0.05, "winner_p_one_sided": round(pp, 5)})

    n_sig = sum(1 for c in corpus if c["winner_significant"])
    print(f"[reddit] {len(corpus)} packages (image x subreddit, >= {MIN_VARIANTS} distinct titles, "
          f">= {MIN_VOTES} votes), {n_sig} significant-winner, "
          f"{sum(len(c['variants']) for c in corpus)} variants")
    if args.dry_run:
        return
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))
    OUT.with_suffix(".manifest.json").write_text(json.dumps({
        "source": "SNAP Reddit submissions (Lakkaraju et al., ICWSM 2013)",
        "source_sha256": src_sha, "lock_date": LOCK_DATE, "min_votes": MIN_VOTES,
        "outcome": "upvote ratio up/(up+down); winner via one-sided two-proportion z (p<0.05)",
        "grouping": "image_id x subreddit (content+community held constant; title varies)",
        "n_packages": len(corpus), "n_packages_significant_winner": n_sig,
        "n_variants": sum(len(c["variants"]) for c in corpus),
        "corpus_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    }, indent=2))
    print(f"[reddit] wrote {OUT}")


if __name__ == "__main__":
    main()
