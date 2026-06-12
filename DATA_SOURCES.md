# Data Sources

The corpora used in the paper are **public third-party datasets**. They are
**not redistributed** in this package, to respect their original licenses. Each
is cited in `latex/references.bib`. The aggregated artifacts under `reports/`
are sufficient to verify every number in the paper **without** re-downloading
the raw data; the steps below are only needed to rebuild `reports/` from
scratch (analysis/deep tiers — see `REPLICATION.md`).

Verify every download against its committed manifest in `datasets/`
(`source_sha256` for the raw file, `corpus_sha256` for the regenerated subset).
All commands run from the repository root.

## 1. Upworthy Research Archive (primary ground truth) — OSF project `jd64p`

Matias et al., *Scientific Data* 2021, DOI `10.1038/s41597-021-00934-7`.
Three splits are used: exploratory (primary), confirmatory, holdout.

```bash
mkdir -p data/upworthy_raw
curl -sL "https://osf.io/download/3vqmp/" -o data/upworthy_raw/upworthy-exploratory.csv   # ~14 MB
curl -sL "https://osf.io/download/vy8mj/" -o data/upworthy_raw/upworthy-confirmatory.csv  # ~66 MB
curl -sL "https://osf.io/download/ynf3k/" -o data/upworthy_raw/upworthy-holdout.csv       # ~14 MB

# verify the exploratory source hash against datasets/upworthy-subset-2026-06-03.manifest.json
sha256sum data/upworthy_raw/upworthy-exploratory.csv
#   expected source_sha256: 8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce

# regenerate the locked corpora (each must match its manifest corpus_sha256)
python scripts/01_ingest_upworthy.py --input data/upworthy_raw/upworthy-exploratory.csv
python scripts/01_ingest_upworthy.py --input data/upworthy_raw/upworthy-confirmatory.csv --name upworthy-confirmatory
python scripts/01_ingest_upworthy.py --input data/upworthy_raw/upworthy-holdout.csv     --name upworthy-holdout
```

> **Citation integrity:** confirm the Upworthy bib entry's authorship against DOI
> `10.1038/s41597-021-00934-7` (Crossref) before any submission. Do not trust
> hand-entered authors.

## 2. MIND — Microsoft News Dataset (cross-domain replication)

Via HuggingFace `jchoi0406/MINDNews` (gated → needs an HF token in `HF_TOKEN`).

```bash
mkdir -p data/mind_raw
export HF_TOKEN="<your-huggingface-token>"
for f in news.tsv behaviors.tsv; do
  curl -sL -H "Authorization: Bearer $HF_TOKEN" \
    "https://huggingface.co/datasets/jchoi0406/MINDNews/resolve/main/$f" -o "data/mind_raw/$f"
done
python scripts/build_mind_corpus.py   # must match datasets/mind-subset-2026-06-03.manifest.json
```

## 3. SNAP Reddit submissions (cross-platform robustness)

Lakkaraju et al., ICWSM 2013.

```bash
mkdir -p data/reddit_raw
curl -sL "http://snap.stanford.edu/data/redditSubmissions.csv.gz" -o data/reddit_raw/redditSubmissions.csv.gz
gunzip -f data/reddit_raw/redditSubmissions.csv.gz
python scripts/build_reddit_corpus.py   # must match datasets/reddit-subset-2026-06-04.manifest.json
```

## Retrieval notes

- Exact citation details are in `latex/references.bib`.
- The locked corpus JSONs are gitignored (large, fully regenerable); only the
  manifests are committed for provenance. `git check-ignore datasets/upworthy-subset-2026-06-03.json`
  confirms the corpora are local-only.
- The system under test is driven by Google Gemini (`gemini-3.1-flash-lite`
  primary, with `gemini-2.5-flash` / `gemini-3.5-flash` cross-tier comparators,
  and OpenAI `gpt-4.1` as a cross-family check). The deep tier needs
  `GEMINI_API_KEY` in the environment — see `REPLICATION.md`.
