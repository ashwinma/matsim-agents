"""Warn (or fail) when AL training frames share a parent with a fixed validation set."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def sidecar_path(validation_set: str | Path) -> Path:
    return Path(validation_set).with_suffix(".parents.json")


def validation_parents(validation_set: str | Path) -> set[str]:
    """Parent ids recorded for a validation set (empty if no sidecar exists)."""
    path = sidecar_path(validation_set)
    if not path.is_file():
        return set()
    rows = json.loads(path.read_text())["frames"]
    return {row["parent_id"] for row in rows if row.get("parent_id")}


def frame_parent(atoms: Any) -> str | None:
    """parent_id from atoms.info, else the seed-file sha256 in an E3 ``generation_json``."""
    atoms = getattr(atoms, "atoms", atoms)
    if atoms.info.get("parent_id"):
        return str(atoms.info["parent_id"])
    try:
        return json.loads(atoms.info["generation_json"]).get("source_sha256")
    except (KeyError, TypeError, ValueError):
        return None


def check_parent_leakage(
    training_frames: Any, validation_set: str | Path, mode: str | None = None
) -> dict[str, int]:
    """Count training frames whose parent also parents validation frames.

    mode (env MATSIM_PARENT_LEAKAGE, default "warn"): off | warn | fail.
    """
    mode = mode or os.environ.get("MATSIM_PARENT_LEAKAGE", "warn")
    if mode == "off":
        return {}
    parents = validation_parents(validation_set)
    if not parents:
        return {}
    shared: dict[str, int] = {}
    for frame in training_frames:
        parent = frame_parent(frame)
        if parent in parents:
            shared[parent] = shared.get(parent, 0) + 1
    if shared:
        message = (
            f"{sum(shared.values())} training frames share a parent with validation set "
            f"{validation_set} (parents: {sorted(shared)}); validation is not parent-independent"
        )
        if mode == "fail":
            raise ValueError(message)
        log.warning(message)
    return shared
