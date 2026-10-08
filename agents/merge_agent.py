from __future__ import annotations

from pathlib import Path

from graph.state import AuditState

def merge_findings(state: AuditState) -> dict:
    repo_root = Path(state["repo_path"]).resolve()

    complexity_files = {
        Path(f.file).resolve().relative_to(repo_root).as_posix()
        for f in state["complexity_findings"]
    }
    churn_files = {Path(f.file).as_posix() for f in state["churn_findings"]}

    cross_flagged = sorted(complexity_files & churn_files)
    return {"cross_flagged_files": cross_flagged}