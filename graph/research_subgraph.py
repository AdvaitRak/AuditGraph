from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from graph.state import AuditState
from agents.complexity_agent import complexity_agent
from agents.churn_agent import churn_agent
from agents.merge_agent import merge_findings  


def build_research_subgraph():
    builder = StateGraph(AuditState)

    builder.add_node("complexity_agent", complexity_agent)
    builder.add_node("churn_agent", churn_agent)
    builder.add_node("merge", merge_findings)

    builder.add_edge(START, "complexity_agent")
    builder.add_edge(START, "churn_agent")

    builder.add_edge("complexity_agent", "merge")
    builder.add_edge("churn_agent", "merge")

    builder.add_edge("merge", END)

    return builder.compile()


if __name__ == "__main__":
    import sys

    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    graph = build_research_subgraph()
    result = graph.invoke({"repo_path": repo_path})

    print("complexity_findings:", result["complexity_findings"])
    print("churn_findings:", result["churn_findings"])
    print("cross_flagged_files:", result["cross_flagged_files"])