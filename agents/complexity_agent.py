from tools.complexity_tool import run_complexity_analysis
from graph.state import AuditState

def complexity_agent(state: AuditState) -> dict:
    
    try:
        result = run_complexity_analysis(state["repo_path"])
    except Exception as e:
        raise RuntimeError(f"Error computing complexity for {state['repo_path']}") from e
    
    return {"complexity_findings": result}
    
