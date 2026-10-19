from tools.lint_tool import run_lint_analysis
from graph.state import AuditState


def lint_agent(state: AuditState) -> dict:
    try:
        result = run_lint_analysis(state["repo_path"])
    except Exception as e:
        raise RuntimeError(f"Error running lint for {state['repo_path']}") from e

    return {"lint_findings": result}