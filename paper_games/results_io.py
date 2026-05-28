"""Helpers for organizing experiment outputs.

Convention for any experiment script in `scripts/`:

    results/<experiment>_<params>_<timestamp>/
        config.json          # all configs + sweep spec + git state, JSON-serialized
        data.csv             # one row per (condition × seed)
        <plot>.png           # the figure(s)

`make_run_dir` produces the directory; `save_config_json` and `save_data_csv`
write the per-run artifacts; `capture_git_state` records the code state
(commit + dirty flag + uncommitted diff) so a run is fully reproducible.
"""
from __future__ import annotations
from dataclasses import asdict, is_dataclass
from datetime import datetime
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


def make_run_dir(
    experiment: str,
    params: str,
    base: str | Path = "results",
    timestamp: str | None = None,
) -> Path:
    """Create and return a fresh per-run directory under ``base``.

    The directory name has the form ``<experiment>_<params>_<timestamp>``.
    Timestamp defaults to the current local time, formatted ``YYYY-MM-DD-HHMM``.
    The directory is created (with parents) if it doesn't already exist.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    base = Path(base)
    path = base / f"{experiment}_{params}_{timestamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_config_json(path: Path, **components: Any) -> None:
    """Serialize one or more configuration objects to JSON.

    Each keyword argument names a sub-object that's serialized under that key.
    Dataclasses are converted recursively via :func:`dataclasses.asdict`; other
    values pass through as-is (must be JSON-serializable).
    """
    payload = {
        key: (asdict(value) if is_dataclass(value) else value)
        for key, value in components.items()
    }
    Path(path).write_text(json.dumps(payload, indent=2, default=str))


def save_data_csv(path: Path, rows: list[dict]) -> None:
    """Write a list of dicts as CSV (one row per dict, keys → columns).

    All rows are assumed to share the same keys (the first row's keys are used
    as the header).
    """
    path = Path(path)
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def capture_git_state(cwd: str | Path | None = None) -> dict:
    """Capture the current git commit + dirty flag for reproducibility.

    Returned dict:
        ``commit``        — full SHA of HEAD (``str`` or ``None`` if unavailable).
        ``commit_short``  — short SHA.
        ``dirty``         — ``True`` if there are uncommitted changes.
        ``status``        — porcelain status output, only when dirty (so the
                            uncommitted state is *recorded*, not lost).
        ``diff``          — full diff against HEAD, only when dirty.
        ``note``          — explanation if capture failed; ``None`` otherwise.

    The script that wrote a "dirty" run can therefore reconstruct the exact code
    state by checking out ``commit`` and re-applying ``diff``.

    If git is missing or the directory isn't a repo, the function does **not**
    raise — it returns a dict with ``note`` set so the record explicitly flags
    "no git state captured" rather than silently omitting it.
    """
    cwd_str = str(cwd) if cwd is not None else None
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=cwd_str,
        ).stdout.strip()
        commit_short = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, cwd=cwd_str,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=cwd_str,
        ).stdout
        is_dirty = bool(status.strip())
        diff = None
        if is_dirty:
            # Capture the diff against HEAD so the dirty state is recoverable.
            diff = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True, text=True, check=True, cwd=cwd_str,
            ).stdout
        return {
            "commit": commit,
            "commit_short": commit_short,
            "dirty": is_dirty,
            "status": status if is_dirty else None,
            "diff": diff,
            "note": None,
        }
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return {
            "commit": None,
            "commit_short": None,
            "dirty": None,
            "status": None,
            "diff": None,
            "note": f"git state capture failed: {type(e).__name__}: {e}",
        }
