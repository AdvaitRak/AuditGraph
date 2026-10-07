from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from tools.complexity_tool import ComplexityFinding
from tools.churn_tool import ChurnFinding

CriticDecision = Literal["accept", "revise", "escalate"]

class AuditState(TypedDict):
    repo_path: str
    active_agents: list[str]
    churn_findings: list[ChurnFinding]
    complexity_findings: list[ComplexityFinding]
    cross_flagged_files: list[str]
    synthesis_draft: str
    critic_decision: CriticDecision
    critic_feedback: str  
    revision_count: int  
    final_report: str
