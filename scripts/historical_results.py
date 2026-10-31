"""Explicit adapter for the immutable 7c1ab46 report schema.

The old kendall_tau/tau fields contain Goodman–Kruskal gamma. This adapter is
only for known historical files, verified against the retained provenance
manifest. Corrected analyses use their own schema and never pass through here.
"""
import csv
import hashlib
import io
import json
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[1] / "reports"
KEYS = {"kendall_tau": "goodman_kruskal_gamma", "tau": "gamma",
        "persona_tau": "persona_gamma", "baseline_tau": "baseline_gamma",
        "gap_tau": "gap_gamma", "tau_sd": "gamma_sd",
        "tau_lo": "gamma_lo", "tau_hi": "gamma_hi"}


def _bytes(name):
    manifest = json.loads((REPORTS / "legacy-provenance.json").read_text())
    if name not in manifest["files"]:
        raise ValueError("not a pinned historical report: " + str(name))
    raw = (REPORTS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["files"][name]:
        raise ValueError("historical report bytes changed: " + name)
    return raw


def _adapt(value):
    if isinstance(value, list):
        return [_adapt(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            renamed = KEYS.get(key, key)
            if renamed in result:
                raise ValueError("ambiguous legacy metric identity")
            result[renamed] = _adapt(item)
        return result
    return value


def read_historical(name):
    return _adapt(json.loads(_bytes(name)))


def historical_csv(name):
    return [_adapt(row) for row in csv.DictReader(io.StringIO(_bytes(name).decode()))]
