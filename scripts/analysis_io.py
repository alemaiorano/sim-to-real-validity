"""Exclusive outputs for corrected analyses; committed legacy reports are read-only."""
import json
from pathlib import Path

HISTORICAL_REPORTS = Path(__file__).resolve().parents[1] / "reports"


def new_output(path):
    path = Path(path).resolve()
    if path.is_relative_to(HISTORICAL_REPORTS.resolve()):
        raise ValueError("historical reports are immutable; select a separate output destination")
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, payload):
    path = new_output(path)
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return path
