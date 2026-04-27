"""
storage.py — Persistent storage layer for candidate data.

Reads / writes candidate profiles to a local JSON file so data
survives across Streamlit re-runs.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")


def _ensure_file() -> None:
    """Create the data directory and file if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CANDIDATES_FILE):
        with open(CANDIDATES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_candidates() -> List[Dict[str, Any]]:
    """Load all candidate records from the JSON file."""
    _ensure_file()
    try:
        with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_candidate(candidate: Dict[str, Any]) -> None:
    """Append a single candidate record and persist to disk."""
    candidates = load_candidates()
    candidate["submitted_at"] = datetime.now(timezone.utc).isoformat()
    candidates.append(candidate)
    with open(CANDIDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)


def export_candidate_json(candidate: Dict[str, Any]) -> str:
    """Return a pretty-printed JSON string of the candidate profile."""
    return json.dumps(candidate, indent=2, ensure_ascii=False)
