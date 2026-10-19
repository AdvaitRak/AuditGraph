from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field

from tools.complexity_tool import ComplexityFinding
from tools.churn_tool import ChurnFinding
from tools.lint_tool import LintFinding

CriticDecision = Literal["accept", "revise", "escalate"]


class FixTarget(BaseModel):
    """One file the fixer should work on, with everything the scanners found about it."""

    file: str  # path relative to the repo root, with forward slashes
    signals: list[str]  # which agents flagged it, e.g. ["complexity", "lint", "churn"]
    complexity_findings: list[ComplexityFinding] = Field(default_factory=list)
    lint_findings: list[LintFinding] = Field(default_factory=list)
    churn: ChurnFinding | None = None


class AuditState(TypedDict):
    repo_path: str
    active_agents: list[str]
    churn_findings: list[ChurnFinding]
    complexity_findings: list[ComplexityFinding]
    lint_findings: list[LintFinding]
    cross_flagged_files: list[str]
    fix_targets: list[FixTarget]
    synthesis_draft: str
    critic_decision: CriticDecision
    critic_feedback: str
    revision_count: int
    final_report: str