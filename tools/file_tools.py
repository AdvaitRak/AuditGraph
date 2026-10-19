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

def search_code(
    repo_root: str,
    pattern: str,
    directory: str = ".",
    max_results: int = MAX_SEARCH_RESULTS,
) -> str:
    """Search .py files for a regex (falls back to plain text if it isn't valid regex)."""
    root = Path(repo_root).resolve()
    base = resolve_in_repo(root, directory)

    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(re.escape(pattern))

    results: list[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in BLOCKED_NAMES)
        for name in sorted(filenames):
            file_path = Path(dirpath) / name
            if file_path.suffix not in SEARCH_SUFFIXES or file_path.is_symlink():
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    results.append(f"{_rel(root, file_path)}:{lineno}: {line.strip()[:200]}")
                    if len(results) >= max_results:
                        return "\n".join(results) + f"\n... stopped at {max_results} matches"

    return "\n".join(results) if results else f"no matches for: {pattern}" 

