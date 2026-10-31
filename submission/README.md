# arXiv source package

Upload **[arxiv-source.tar.gz](arxiv-source.tar.gz)** as the TeX source archive. Select
**PDFLaTeX** and `main.tex` as the entry point. The archive has `main.tex` at its root,
the section/table/macro sources, PDF figures, `references.bib`, and the generated `main.bbl`.
It excludes the compiled article PDF, build logs, repository history, raw observations and
internal review records. The archive has no dependence on a provider account or local repo.

From the repository root, regenerate with:

```bash
make arxiv
cd submission
sha256sum -c arxiv-source.sha256
```

`arxiv-source.manifest.json` pins every archive member and the canonical PDF hash. Extract
into an empty directory and build there with PDFLaTeX/BibTeX; with the recorded toolchain and
`SOURCE_DATE_EPOCH=1793404800`, the result matches `latex/main.pdf` byte for byte. Other TeX
Live versions can change PDF bytes without changing the article's content.

The archive follows the [arXiv TeX submission guidance](https://info.arxiv.org/help/submit_tex.html).
The upload workflow still requires checking arXiv's generated preview before completing submission.
Creating this package does not upload or submit the paper.
