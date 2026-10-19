from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from git import Repo

from graph.state import AuditState, FixTarget
from safety.sandbox import SandboxError, resolve_for_edit


INVESTIGATORS = {"complexity", "lint"}


def _relative(root: Path, path: Path) -> str | None:
    """Path relative to the repo root (forward slashes), or None if outside it."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def _git_root(repo_root: Path) -> Path | None:
    try:
        repo = Repo(repo_root, search_parent_directories=True)
        return Path(repo.working_tree_dir).resolve()
    except Exception:
        return None


def _editable(repo_root: Path, rel: str) -> bool:
    """Can the fixer legally edit this file? (same rules as the edit tool)"""
    try:
        resolve_for_edit(repo_root, rel)
        return True
    except SandboxError:
        return False


def _rank_key(target: FixTarget):
    investigators = len(INVESTIGATORS & set(target.signals))
    bugfix_rate = target.churn.bugfix_rate if target.churn else 0.0
    total_findings = len(target.complexity_findings) + len(target.lint_findings)
    return (-investigators, -bugfix_rate, -total_findings, target.file)


def merge_findings(state: AuditState) -> dict:
    repo_root = Path(state["repo_path"]).resolve()
    git_root = _git_root(repo_root)

    # Group every agent's findings by repo-relative file path, so that the
    # three different path styles (radon, ruff, git) line up.
    complexity_by_file = defaultdict(list)
    for finding in state.get("complexity_findings", []):
        rel = _relative(repo_root, Path(finding.file))
        if rel:
            complexity_by_file[rel].append(finding)

    lint_by_file = defaultdict(list)
    for finding in state.get("lint_findings", []):
        rel = _relative(repo_root, Path(finding.file))
        if rel:
            lint_by_file[rel].append(finding)

    # git reports paths relative to the git root, which may differ from repo_path.
    churn_by_file = {}
    if git_root is not None:
        for finding in state.get("churn_findings", []):
            rel = _relative(repo_root, git_root / finding.file)
            if rel:
                churn_by_file[rel] = finding

    candidates = set(complexity_by_file) | set(lint_by_file)

    targets: list[FixTarget] = []
    for rel in candidates:
        if not _editable(repo_root, rel):
            continue

        signals = []
        if rel in complexity_by_file:
            signals.append("complexity")
        if rel in lint_by_file:
            signals.append("lint")
        if rel in churn_by_file:
            signals.append("churn")

        targets.append(
            FixTarget(
                file=rel,
                signals=signals,
                complexity_findings=complexity_by_file.get(rel, []),
                lint_findings=lint_by_file.get(rel, []),
                churn=churn_by_file.get(rel),
            )
        )

    targets.sort(key=_rank_key)

    return {
        "fix_targets": targets,
        # Files flagged by at least two different agents, best first.
        "cross_flagged_files": [t.file for t in targets if len(t.signals) >= 2],
    }