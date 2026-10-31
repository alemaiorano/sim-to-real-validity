"""Package the tracked LaTeX inputs and freshly built bibliography for arXiv."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LATEX = ROOT / "latex"
OUTPUT = ROOT / "submission"


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", "latex"], cwd=ROOT)
    sources = {ROOT / os.fsdecode(name) for name in tracked.split(b"\0") if name}
    sources.discard(LATEX / "main.pdf")
    sources.add(LATEX / "main.bbl")
    payload = {}
    for path in sorted(sources):
        if path.is_symlink() or not path.is_file():
            raise ValueError("missing or symlinked paper input: " + str(path))
        name = path.relative_to(LATEX).as_posix()
        if path.suffix not in {".tex", ".bib", ".bbl", ".pdf"}:
            raise ValueError("review unsupported paper input before packaging: " + name)
        payload[name] = path.read_bytes()
    if not {"main.tex", "main.bbl", "references.bib"} <= payload.keys():
        raise ValueError("build the paper and bibliography with make arxiv first")

    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "1793404800"))
    OUTPUT.mkdir(exist_ok=True)
    archive = OUTPUT / "arxiv-source.tar.gz"
    with archive.open("wb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                for name, data in payload.items():
                    entry = tarfile.TarInfo(name)
                    entry.size, entry.mode, entry.mtime = len(data), 0o644, epoch
                    tar.addfile(entry, io.BytesIO(data))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUTPUT / "arxiv-source.sha256").write_text(digest + "  " + archive.name + "\n")
    manifest = {
        "entrypoint": "main.tex", "engine": "pdflatex", "SOURCE_DATE_EPOCH": epoch,
        "archive_sha256": digest,
        "paper_pdf_sha256": hashlib.sha256((LATEX / "main.pdf").read_bytes()).hexdigest(),
        "files": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in payload.items()],
    }
    (OUTPUT / "arxiv-source.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Packaged {len(payload)} paper inputs into {archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
