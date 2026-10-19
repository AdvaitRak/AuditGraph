from __future__ import annotations

from pathlib import Path

BLOCKED_NAMES = {".git", ".env", ".venv", "venv", "__pycache__", "node_modules"}

PROTECTED_TEST_DIRS = {"tests", "test"}


class SandboxError(Exception):
    """Raised when the agent asks for a path it is not allowed to touch."""


def resolve_in_repo(repo_root: str | Path, relative_path: str) -> Path:
    """
    Turn a path given by the LLM into a safe absolute path inside repo_root.

    Raises SandboxError if the path escapes the repo or touches a blocked name.
    """
    root = Path(repo_root).resolve()

    candidate = (root / relative_path).resolve()

    if not candidate.is_relative_to(root):
        raise SandboxError(f"path escapes the repository: {relative_path}")

    for part in candidate.relative_to(root).parts:
        if part in BLOCKED_NAMES:
            raise SandboxError(f"access to '{part}' is not allowed: {relative_path}")

    return candidate


def _is_test_file(path: Path) -> bool:
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def resolve_for_edit(repo_root: str | Path, relative_path: str) -> Path:
    """
    Same checks as resolve_in_repo, plus the extra rules for WRITING:
    only existing .py files, and never test files.
    """
    root = Path(repo_root).resolve()
    target = resolve_in_repo(root, relative_path)

    folders = target.relative_to(root).parts[:-1]
    if any(folder in PROTECTED_TEST_DIRS for folder in folders) or _is_test_file(target):
        raise SandboxError(f"test files cannot be edited: {relative_path}")

    if target.suffix != ".py":
        raise SandboxError(f"only .py files can be edited: {relative_path}")

    if not target.is_file():
        raise SandboxError(f"can only edit existing files: {relative_path}")

    return target