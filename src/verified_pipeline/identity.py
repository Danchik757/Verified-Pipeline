"""Content-based identity for a stage of a reproducible experiment.

This module deliberately contains no scientific defaults. It identifies a
fully resolved stage specification; it does not approve that specification.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*\Z")


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 of file bytes without loading the file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: Any, where: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{where}: non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_value(item, f"{where}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{where}: object key is not a string")
            _json_value(item, f"{where}.{key}")
        return
    raise ValueError(f"{where}: unsupported value type {type(value).__name__}")


def _hash_map(value: Any, where: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{where}: expected a non-empty object")
    for name, digest in value.items():
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError(f"{where}: invalid name {name!r}")
        if not isinstance(digest, str) or not pattern.fullmatch(digest):
            raise ValueError(f"{where}.{name}: invalid lowercase hash")


def validate_stage_spec(spec: Any) -> dict[str, Any]:
    """Validate the exact v1 stage identity contract and return its object."""
    if not isinstance(spec, dict):
        raise ValueError("stage specification must be an object")
    required = {"schema_version", "stage", "code_commits", "input_sha256", "parameters", "upstream_run_ids"}
    if set(spec) != required:
        raise ValueError(f"stage specification keys must be {sorted(required)}")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if not isinstance(spec["stage"], str) or not _NAME.fullmatch(spec["stage"]):
        raise ValueError("stage must be a simple non-empty name")
    _hash_map(spec["code_commits"], "code_commits", _HEX40)
    _hash_map(spec["input_sha256"], "input_sha256", _HEX64)
    if not isinstance(spec["parameters"], dict):
        raise ValueError("parameters must be an object")
    _json_value(spec["parameters"], "parameters")
    upstream = spec["upstream_run_ids"]
    if not isinstance(upstream, list) or any(not isinstance(x, str) or not _HEX64.fullmatch(x) for x in upstream):
        raise ValueError("upstream_run_ids must be a list of lowercase SHA-256 values")
    if len(upstream) != len(set(upstream)):
        raise ValueError("upstream_run_ids contains duplicates")
    return spec


def stage_run_id(spec: Any) -> str:
    """Hash canonical JSON of an explicitly resolved stage specification."""
    valid = validate_stage_spec(spec)
    encoded = json.dumps(valid, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
