from __future__ import annotations

import os
import re
from pathlib import Path

from safety.sandbox import BLOCKED_NAMES, resolve_in_repo

MAX_LIST_ENTRIES = 200
MAX_READ_LINES = 300
MAX_SEARCH_RESULTS = 30
SEARCH_SUFFIXES = {".py"}


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def list_files(repo_root: str, directory: str = ".") -> str:
    """List the entries of a folder inside the repo (folders end with '/')."""
    root = Path(repo_root).resolve()
    target = resolve_in_repo(root, directory)
    if not target.is_dir():
        raise NotADirectoryError(f"not a directory: {directory}")

    entries = []
    for child in sorted(target.iterdir()):
        if child.name in BLOCKED_NAMES:
            continue
        entries.append(_rel(root, child) + ("/" if child.is_dir() else ""))

    if not entries:
        return "(empty directory)"

    text = "\n".join(entries[:MAX_LIST_ENTRIES])
    if len(entries) > MAX_LIST_ENTRIES:
        text += f"\n... {len(entries) - MAX_LIST_ENTRIES} more entries not shown"
    return text