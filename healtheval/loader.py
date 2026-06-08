from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from .models import FailureMode

_PACKAGE_DIR = Path(__file__).parent.parent
_FAILURE_MODES_DIRS = [
    _PACKAGE_DIR / "failure_modes",
    Path.cwd() / "failure_modes",
    Path(os.environ.get("HEALTHEVAL_FAILURE_MODES_DIR", "failure_modes")),
]


def _find_failure_modes_dir() -> Path:
    for d in _FAILURE_MODES_DIRS:
        if d.exists() and d.is_dir():
            return d
    raise FileNotFoundError(
        f"failure_modes/ directory not found. Searched: {_FAILURE_MODES_DIRS}. "
        f"Set HEALTHEVAL_FAILURE_MODES_DIR env var to specify a custom path."
    )


def _load_all_dicts() -> List[Dict[str, Any]]:
    fmdir = _find_failure_modes_dir()
    all_modes = []
    for yaml_file in sorted(fmdir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if isinstance(content, list):
                all_modes.extend(content)
            elif isinstance(content, dict):
                all_modes.append(content)
    return all_modes


def load_failure_mode(failure_mode_id: str) -> FailureMode:
    """Load a single failure mode by ID (e.g. 'SCRIBE-001')."""
    for mode_dict in _load_all_dicts():
        if mode_dict.get("id") == failure_mode_id:
            return FailureMode.from_dict(mode_dict)
    available = [d.get("id") for d in _load_all_dicts()]
    raise ValueError(
        f"Failure mode '{failure_mode_id}' not found. "
        f"Available: {available}"
    )


def load_all_failure_modes() -> List[FailureMode]:
    """Load all failure modes from all YAML files in failure_modes/."""
    return [FailureMode.from_dict(d) for d in _load_all_dicts()]


def load_by_category(category: str) -> List[FailureMode]:
    """Load all failure modes for a given category."""
    return [
        FailureMode.from_dict(d)
        for d in _load_all_dicts()
        if d.get("category") == category
    ]


def list_failure_modes() -> List[Dict[str, str]]:
    """Return summary list of all failure modes."""
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "category": d["category"],
            "severity": d["severity"],
        }
        for d in _load_all_dicts()
    ]
