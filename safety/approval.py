from __future__ import annotations

import difflib
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalResult:
    approved: bool
    feedback: str = ""   


def make_diff(path: str, original: str, proposed: str) -> str:
    """Unified diff (like `git diff`) between the current and the proposed file."""
    lines = difflib.unified_diff(
        original.splitlines(),
        proposed.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
        n=3,
    )
    return "\n".join(lines)


def request_approval(path: str, original: str, proposed: str) -> ApprovalResult:
    """Show the diff and ask the human. Anything other than a clear 'yes' is a rejection."""
    if original == proposed:
        return ApprovalResult(False, "the proposed content is identical to the current file")

    # Safe default: if nobody can answer (script, pipe, CI), never auto-approve.
    if not sys.stdin.isatty():
        return ApprovalResult(False, "no human available to approve edits")

    print("\n" + "=" * 70)
    print(f"PROPOSED EDIT: {path}")
    print("=" * 70)
    print(make_diff(path, original, proposed))
    print("=" * 70)

    answer = input(
        "Apply this change? [y = approve, n = reject, or type a reason to reject]: "
    ).strip()

    if answer.lower() in {"y", "yes"}:
        return ApprovalResult(True)
    if answer.lower() in {"", "n", "no"}:
        return ApprovalResult(False, "rejected by the human reviewer")
    return ApprovalResult(False, f"rejected by the human reviewer: {answer}")