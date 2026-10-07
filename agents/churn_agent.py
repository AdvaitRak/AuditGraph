from tools.churn_tool import run_churn_analysis
from graph.state import AuditState

def churn_agent(state: AuditState) -> dict:
    
    repo_path = state.get("repo_path")
    try:
        result = run_churn_analysis(repo_path)
    except Exception as e:
        raise RuntimeError(f"Error computing churn for {repo_path}") from e

    return {"churn_findings": result}
    