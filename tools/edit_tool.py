from __future__ import annotations

import ast
import difflib
from datetime import datetime
from pathlib import Path

from safety.approval import request_approval
from safety.sandbox import resolve_for_edit

BACKUP_DIR = Path("logs") / "backups"
MAX_CHANGED_LINES = 60


class EditError(Exception):
    """The proposed edit is invalid or unsafe, and was NOT applied."""


def _describe(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    decorators = ", ".join(ast.unparse(d) for d in node.decorator_list)
    returns = ast.unparse(node.returns) if node.returns else ""
    return f"{prefix}@[{decorators}] ({ast.unparse(node.args)}) -> {returns}"


def _collect_signatures(tree: ast.Module) -> dict[str, str]:
    """Signatures of top-level functions, classes and class methods."""
    sigs: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sigs[node.name] = _describe(node)
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            sigs[node.name] = f"class({bases})"
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sigs[f"{node.name}.{item.name}"] = _describe(item)
    return sigs


def _check_python(original: str, proposed: str) -> None:
    """The result must be valid Python and must keep every existing signature."""
    try:
        new_tree = ast.parse(proposed)
    except SyntaxError as e:
        raise EditError(
            f"edit rejected: the result is not valid Python ({e.msg}, line {e.lineno})"
        ) from e

    try:
        old_tree = ast.parse(original)
    except SyntaxError:
        return  # the original was already broken; nothing to compare against

    old_sigs = _collect_signatures(old_tree)
    new_sigs = _collect_signatures(new_tree)

    removed = sorted(set(old_sigs) - set(new_sigs))
    changed = sorted(n for n in old_sigs if n in new_sigs and old_sigs[n] != new_sigs[n])
    if removed or changed:
        raise EditError(
            "edit rejected: it changes the public structure of the file "
            f"(removed: {removed or 'none'}; signature changed: {changed or 'none'}). "
            "Keep existing function/class names, parameters and decorators unchanged."
        )


def _count_changed_lines(original: str, proposed: str) -> int:
    diff = difflib.unified_diff(original.splitlines(), proposed.splitlines(), n=0, lineterm="")
    return sum(
        1
        for line in diff
        if (line.startswith("+") and not line.startswith("+++"))
        or (line.startswith("-") and not line.startswith("---"))
    )


def _backup(rel_path: str, raw_bytes: bytes) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"{rel_path.replace('/', '__')}.{stamp}.bak"
    backup.write_bytes(raw_bytes)
    return backup


def edit_file(repo_root: str, path: str, old_text: str, new_text: str) -> str:
    """
    Replace one exact piece of text in a .py file, after safety checks and human approval.

    Raises EditError if the edit is invalid or unsafe.
    Returns a message describing what happened (applied, or rejected by the human).
    """
    root = Path(repo_root).resolve()
    target = resolve_for_edit(root, path)
    rel = target.relative_to(root).as_posix()

    if not old_text:
        raise EditError("old_text must not be empty")
    if old_text == new_text:
        raise EditError("old_text and new_text are identical; nothing to change")

    raw_bytes = target.read_bytes()
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise EditError(f"{rel} is not valid UTF-8 text") from e

    # Work with "\n" internally, and restore Windows line endings when writing,
    # so an edit never rewrites the line endings of the whole file.
    uses_crlf = "\r\n" in raw
    original = raw.replace("\r\n", "\n")

    count = original.count(old_text)
    if count == 0:
        raise EditError(
            "old_text was not found in the file. Copy it exactly from the read_file "
            "output, WITHOUT the line-number prefix."
        )
    if count > 1:
        raise EditError(
            f"old_text matches {count} places. Include more surrounding lines "
            "so that it matches exactly one place."
        )

    proposed = original.replace(old_text, new_text, 1)

    _check_python(original, proposed)

    changed = _count_changed_lines(original, proposed)
    if changed > MAX_CHANGED_LINES:
        raise EditError(
            f"edit too large ({changed} changed lines, limit {MAX_CHANGED_LINES}). "
            "Make a smaller change."
        )

    decision = request_approval(rel, original, proposed)
    if not decision.approved:
        return f"Edit NOT applied: {decision.feedback}"

    backup = _backup(rel, raw_bytes)
    output = proposed.replace("\n", "\r\n") if uses_crlf else proposed
    target.write_bytes(output.encode("utf-8"))

    return f"Edit applied to {rel} ({changed} changed lines). Backup: {backup.as_posix()}"