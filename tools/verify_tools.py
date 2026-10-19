from __future__ import annotations

import ast
from pathlib import Path

from safety.sandbox import resolve_in_repo
from tools.complexity_tool import RANK_ORDER, run_complexity_analysis
from tools.lint_tool import run_lint_analysis


def _resolve_python_file(repo_root: str, path: str) -> tuple[Path, Path, str]:
    root = Path(repo_root).resolve()
    target = resolve_in_repo(root, path)
    if not target.is_file() or target.suffix != ".py":
        raise ValueError(f"not an existing .py file: {path}")
    return root, target, target.relative_to(root).as_posix()


def check_syntax(repo_root: str, path: str) -> str:
    """Is the file valid Python? (Parses it; never runs it.)"""
    _, target, rel = _resolve_python_file(repo_root, path)
    source = target.read_text(encoding="utf-8", errors="replace")
    try:
        ast.parse(source)
    except SyntaxError as e:
        return f"SYNTAX ERROR in {rel}, line {e.lineno}: {e.msg}"
    return f"OK: {rel} is valid Python"


def check_complexity(repo_root: str, path: str, min_rank: str = "C") -> str:
    """Re-run radon on one file: which functions are still at min_rank or worse?"""
    _, target, rel = _resolve_python_file(repo_root, path)
    if min_rank not in RANK_ORDER:
        raise ValueError(f"min_rank must be one of {RANK_ORDER}")

    findings = run_complexity_analysis(str(target), min_rank=min_rank)
    if not findings:
        return f"No functions at rank {min_rank} or worse in {rel}."

    lines = [
        f"[{f.rank}] {rel}:{f.line_number} {f.function_name} (complexity={f.complexity_score})"
        for f in findings
    ]
    return f"Functions at rank {min_rank} or worse in {rel}:\n" + "\n".join(lines)


def run_lint(repo_root: str, path: str) -> str:
    """Run ruff (defect rules) on one file."""
    _, target, rel = _resolve_python_file(repo_root, path)
    findings = run_lint_analysis(str(target), limit=50)
    if not findings:
        return f"No lint problems found in {rel}"
    return "\n".join(f"{rel}:{f.line_number} [{f.rule}] {f.message}" for f in findings)