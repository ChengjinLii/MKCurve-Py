# Adapted from SlicerDSpace microstructure/dki.py, BSD-3-Clause.
# Copyright (c) 2026, Chengjin Li and the SlicerDSpace contributors.
"""Minimal, standalone shell grouping and provenance I/O."""

import hashlib
import json
from pathlib import Path
import tempfile


def _shells(bvals, threshold, tolerance):
    shells = []
    for index in sorted((i for i, b in enumerate(bvals) if b > threshold), key=lambda i: bvals[i]):
        if not shells or bvals[index] - bvals[shells[-1][0]] > tolerance:
            shells.append([])
        shells[-1].append(index)
    return shells


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, suffix=".json", encoding="utf-8", delete=False) as stream:
        staged = Path(stream.name)
        try:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        except Exception:
            staged.unlink(missing_ok=True)
            raise
    try:
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def _signature(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    stat = path.stat()
    return {"path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest.hexdigest()}
