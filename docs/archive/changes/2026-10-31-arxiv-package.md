# Reproducible arXiv source archive

Base f4a3219831a4ad1504b23416259ec57762b189a1. The paper source/PDF already exists on main;
this change distributes a ready source archive and a repeatable packaging step. The user accepts
tar.gz and authorizes validation and merge into the paper repository's main branch.

The existing Make reproduce owner now builds the archive after PDFLaTeX/BibTeX. Make arxiv is
an alias for that same pipeline. The standard-library packager reads tracked LaTeX inputs,
adds the freshly compiled main.bbl, excludes the article PDF and build intermediates, and uses
relative root paths and normalized timestamps/permissions. A manifest and SHA256 accompany it.

Validation extracts the actual archive into a separate empty directory, checks every member,
compiles without repository/data/model access and compares the resulting PDF with the unchanged
canonical paper. A clean checkout must regenerate identical paper/archive/manifest bytes and
pass the public payload catalog. Existing scientific/data/bibliography audit evidence is reused
only for unchanged source hashes. No new model calls or unrelated statistical suite is needed.

Submission preparation does not publish to arXiv. The current package, source history and
validation evidence are retained outside worktrees and in protected backups/Windows OneDrive.
