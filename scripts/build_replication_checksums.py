"""Catalog Git-tracked replication payload, excluding the checksum file itself.

Stage intended new files before running. Ignored raw data, credentials and local outputs
are not selected. The Git commit authenticates this file list and the checksum catalog.
"""
import hashlib
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "REPLICATION_SHA256SUMS"


def main():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    rows = []
    for name in sorted(os.fsdecode(n) for n in names if n):
        if name == CATALOG:
            continue
        path = ROOT / name
        if any(c in name for c in "\n\r\\") or path.is_symlink() or not path.is_file():
            raise ValueError("unsupported checksum payload path: " + name)
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            raise ValueError("credential file cannot be replication payload")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        rows.append(digest + "  " + name + "\n")
    (ROOT / CATALOG).write_text("".join(rows), encoding="utf-8")
    print(f"Catalogued {len(rows)} tracked payload files; catalog identity is recorded by Git.")


if __name__ == "__main__":
    main()
