# Data sources and versioned ingestion

Corpora are public third-party sources and are not redistributed. Original manifests under
`datasets/` remain evidence of the original locks; changing analysis code does not rewrite them.
Reexporting aggregated reports is distinct from regenerating corpora or recomputing statistics.

## Upworthy

Matias et al., Scientific Data (2021), DOI
[10.1038/s41597-021-00934-7](https://doi.org/10.1038/s41597-021-00934-7),
[OSF project](https://osf.io/jd64p/).

```bash
mkdir -p data/upworthy_raw
curl -fL https://osf.io/download/3vqmp/ -o data/upworthy_raw/upworthy-exploratory.csv
curl -fL https://osf.io/download/vy8mj/ -o data/upworthy_raw/upworthy-confirmatory.csv
curl -fL https://osf.io/download/ynf3k/ -o data/upworthy_raw/upworthy-holdout.csv
sha256sum data/upworthy_raw/upworthy-exploratory.csv
```

The original exploratory source SHA256 is
`8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce`.
The original derived corpus SHA256 is
`523034f1fd86d4a432a57b29eb25230418dba119c3367ec04622815114cc9f85`.

For exact historical restoration, use the producer at pinned commit
`7c1ab46b5d881529b79769fb870ed1f2fb98619c` in a separate checkout, then verify the
original manifest. The revised builder intentionally produces a **different schema/hash**:

```bash
python scripts/01_ingest_upworthy.py --input data/upworthy_raw/upworthy-exploratory.csv \
  --output-dir /new/path/upworthy-corrected
```

It retains the same headline/count construction and supplies the corrected winner policy.
The correction check recovered 1,695 packages/6,978 variants with identical original variant
data, and 190 passing packages. A new manifest accompanies the new corpus.
Do not substitute this file for the original corpus in historical hash checks.

## MIND

Wu et al., ACL 2020, DOI
[10.18653/v1/2020.acl-main.331](https://aclanthology.org/2020.acl-main.331/).
Primary dataset information: [Microsoft News Dataset](https://msnews.github.io/).
The historical package used the HuggingFace `jchoi0406/MINDNews` mirror; access is subject to
that host's current terms. Restore `news.tsv` and `behaviors.tsv` under `data/mind_raw/`
and verify the historical manifest. The combined source hash uses file bytes in news/behaviors order.

```bash
python scripts/build_mind_corpus.py --output-dir /new/path/mind-corrected
```

## Reddit reposts

Lakkaraju, McAuley, and Leskovec, ICWSM 2013, DOI
[10.1609/icwsm.v7i1.14408](https://ojs.aaai.org/index.php/ICWSM/article/view/14408).
The publisher portal shows a later migration date; the proceedings are from 2013.
Dataset: [SNAP Reddit submissions](https://snap.stanford.edu/data/web-Reddit.html).

Restore the source CSV under `data/reddit_raw/redditSubmissions.csv` and verify its original
manifest before use.

```bash
python scripts/build_reddit_corpus.py --output-dir /new/path/reddit-corrected
```

This grouping is observational and does not isolate causal title effects. The original manifest
has 5,393 selected packages, while evaluated historical coverage is 600 panel/599 baseline.
The released artifacts do not document that subset-selection procedure.

## Preservation and availability

New builders require an absent destination directory and preserve historical locks.
Only manifests, not full corpora, are committed. The GPT scalar checkpoint needed for the
offline diagnostic is not a third-party public corpus and is not distributed here.
Exact input hashes and commands are in REPLICATION. New generation cannot recover missing
historical observations exactly.
