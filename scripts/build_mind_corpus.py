#!/usr/bin/env python3
"""Adapt the MIND dataset (Microsoft News, Nov 2019) into the sim-to-real corpus schema, as a
DIFFERENT-characteristic, more-recent benchmark than Upworthy.

Adaptation + caveat: MIND is personalized news recommendation, not a controlled copy A/B. We
aggregate real impressions/clicks per headline across all logs, then group headlines by
SUBCATEGORY (topic-controlled "packages"); within a package we rank by aggregate CTR. This tests
real headline clickability in a recent, different domain; unlike Upworthy it compares DIFFERENT
articles within a topic, so content (not only wording) varies — documented as a threat.

Output: datasets/mind-subset-<DATE>.json (same schema: packages -> variants with
headline, impressions, clicks, real_ctr; winner_significant tag). Fails loudly if inputs absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

SEED = 42
LOCK_DATE = "2026-06-03"
MIN_IMPRESSIONS = 200      # per-headline, for CTR reliability (MIND per-article counts are lower than Upworthy)
MIN_VARIANTS = 2
MAX_VARIANTS_PER_PKG = 10  # cap a subcategory package to its top-N by impressions (keep comparisons tight)
PAPER_DIR = Path(__file__).resolve().parents[1]
RAW = PAPER_DIR / "data" / "mind_raw"
OUT = PAPER_DIR / "datasets" / f"mind-subset-{LOCK_DATE}.json"


def fail(m): print(f"[mind][FATAL] {m}", file=sys.stderr); sys.exit(1)


def p_one(c1, n1, c2, n2):
    p = (c1 + c2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1/n1 + 1/n2))
    return 1.0 if se == 0 else 0.5 * (1 - math.erf(((c1/n1 - c2/n2)/se) / math.sqrt(2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="only print viability counts")
    args = ap.parse_args()
    news_f, beh_f = RAW / "news.tsv", RAW / "behaviors.tsv"
    if not (news_f.exists() and beh_f.exists()):
        fail(f"missing MIND files in {RAW}")

    # news_id -> (subcategory, title)
    meta = {}
    raw_news = news_f.read_bytes()
    for line in raw_news.decode("utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 4:
            meta[p[0]] = (p[2], p[3])

    # aggregate impressions/clicks per news_id from behaviors
    imp = {}; clk = {}
    raw_beh = beh_f.read_bytes()
    for line in raw_beh.decode("utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        for tok in parts[4].split():
            if "-" not in tok:
                continue
            nid, lab = tok.rsplit("-", 1)
            imp[nid] = imp.get(nid, 0) + 1
            if lab == "1":
                clk[nid] = clk.get(nid, 0) + 1
    src_sha = hashlib.sha256(raw_news + raw_beh).hexdigest()

    # group by subcategory
    bysub = {}
    for nid, i in imp.items():
        if i < MIN_IMPRESSIONS or nid not in meta:
            continue
        sub, title = meta[nid]
        if not title.strip():
            continue
        bysub.setdefault(sub, []).append({
            "variant_id": nid, "headline": title.strip(),
            "impressions": i, "clicks": clk.get(nid, 0),
            "real_ctr": clk.get(nid, 0) / i,
        })

    corpus = []
    for sub, vs in sorted(bysub.items()):
        vs = sorted(vs, key=lambda v: -v["impressions"])[:MAX_VARIANTS_PER_PKG]
        if len(vs) < MIN_VARIANTS:
            continue
        ordered = sorted(vs, key=lambda v: -v["real_ctr"])
        pp = p_one(ordered[0]["clicks"], ordered[0]["impressions"],
                   ordered[1]["clicks"], ordered[1]["impressions"])
        corpus.append({"package_id": f"sub:{sub}", "subcategory": sub, "variants": vs,
                       "winner_significant": pp < 0.05, "winner_p_one_sided": round(pp, 5)})

    n_sig = sum(1 for c in corpus if c["winner_significant"])
    print(f"[mind] {len(corpus)} subcategory-packages (>= {MIN_VARIANTS} headlines, "
          f">= {MIN_IMPRESSIONS} impressions), {n_sig} with a significant winner; "
          f"{sum(len(c['variants']) for c in corpus)} variants")
    if args.dry_run:
        return
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))
    (OUT.with_suffix(".manifest.json")).write_text(json.dumps({
        "source": "MIND (Microsoft News Dataset, Nov 2019) via HF jchoi0406/MINDNews",
        "source_sha256": src_sha, "lock_date": LOCK_DATE, "seed": SEED,
        "min_impressions": MIN_IMPRESSIONS, "max_variants_per_pkg": MAX_VARIANTS_PER_PKG,
        "grouping": "by news subcategory (topic-controlled); compares different articles (caveat)",
        "n_packages": len(corpus), "n_packages_significant_winner": n_sig,
        "n_variants": sum(len(c["variants"]) for c in corpus),
        "corpus_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    }, indent=2))
    print(f"[mind] wrote {OUT}")


if __name__ == "__main__":
    main()
