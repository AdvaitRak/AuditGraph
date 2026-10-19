from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from graph.state import AuditState
from agents.complexity_agent import complexity_agent
from agents.churn_agent import churn_agent
from agents.merge_agent import merge_findings  
from agents.lint_agent import lint_agent


def build_research_subgraph():
    builder = StateGraph(AuditState)

    builder.add_node("complexity_agent", complexity_agent)
    builder.add_node("churn_agent", churn_agent)
    builder.add_node("lint_agent", lint_agent)
    builder.add_node("merge", merge_findings)

    builder.add_edge(START, "complexity_agent")
    builder.add_edge(START, "churn_agent")
    builder.add_edge(START, "lint_agent")

    builder.add_edge("complexity_agent", "merge")
    builder.add_edge("churn_agent", "merge")
    builder.add_edge("lint_agent", "merge")

    builder.add_edge("merge", END)

    return builder.compile()


if __name__ == "__main__":
    import sys

    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    graph = build_research_subgraph()
    result = graph.invoke({"repo_path": repo_path})

    print(f"\n=== complexity_agent: {len(result['complexity_findings'])} finding(s) ===")
    for f in result["complexity_findings"]:
        print(f"  [{f.rank}] {f.file}:{f.line_number} {f.function_name} (complexity={f.complexity_score})")

    print(f"\n=== churn_agent: {len(result['churn_findings'])} finding(s) ===")
    for f in result["churn_findings"]:
        print(f"  {f.file}: {f.total_commits} commits, {f.bugfix_commits} bugfixes ({f.bugfix_rate:.0%})")

    print(f"\n=== lint_agent: {len(result['lint_findings'])} finding(s) ===")
    for f in result["lint_findings"]:
        print(f"  {f.file}:{f.line_number} [{f.rule}] {f.message}")

    print(f"\n=== merge: {len(result['fix_targets'])} fix target(s), best first ===")
    for t in result["fix_targets"]:
        print(f"  {t.file}  signals={t.signals}")

    print("\ncross_flagged_files:", result["cross_flagged_files"])