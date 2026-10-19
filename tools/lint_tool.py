from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

# Defect-level rule families only (no style rules):
#   F  = pyflakes: undefined names, unused imports and variables
#   B  = flake8-bugbear: likely bugs (e.g. mutable default arguments)
#   S  = flake8-bandit: security (eval, hardcoded secrets, shell injection)
#   E9 = syntax errors and runtime errors
DEFECT_RULES = "F,B,S,E9"

IGNORED_RULES = "S101"

RUFF_TIMEOUT_SECONDS = 60


class LintFinding(BaseModel):
    file: str
    line_number: int = Field(ge=0)
    rule: str      
    message: str


def run_lint_analysis(target_path: str, limit: int = 30) -> list[LintFinding]:
    """
    Run ruff (defect-level rules only) on a file or directory.

    Returns findings with the files that have the most problems first.

    Raises:
        FileNotFoundError if target_path doesn't exist.
        RuntimeError if ruff isn't installed, fails, or its output can't be parsed.
    """
    path = Path(target_path)
    if not path.exists():
        raise FileNotFoundError(f"target_path does not exist: {target_path}")

    
    cmd = [
        sys.executable, "-I", "-m", "ruff", "check",
        "--isolated", "--no-cache",
        "--select", DEFECT_RULES,
        "--ignore", IGNORED_RULES,
        "--output-format", "json",
        str(path),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=RUFF_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ruff timed out after {RUFF_TIMEOUT_SECONDS}s on {target_path}") from e

    if "No module named ruff" in result.stderr:
        raise RuntimeError("ruff is not installed; run: pip install ruff")

    if result.returncode not in (0, 1):
        raise RuntimeError(f"ruff failed on {target_path}: {result.stderr.strip()[:500]}")

    try:
        raw = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"could not parse ruff output for {target_path}: {e}\n"
            f"raw stdout: {result.stdout[:500]}"
        ) from e

    findings = [
        LintFinding(
            file=item["filename"],
            line_number=max(item["location"]["row"], 0),
            rule=item.get("code") or "syntax-error",
            message=item["message"],
        )
        for item in raw
    ]

    counts = Counter(f.file for f in findings)
    findings.sort(key=lambda f: (-counts[f.file], f.file, f.line_number))
    return findings[:limit]


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = run_lint_analysis(target)

    if not results:
        print(f"No defect-level lint findings in {target}")
    else:
        print(f"Found {len(results)} lint finding(s):\n")
        for f in results:
            print(f"  {f.file}:{f.line_number} [{f.rule}] {f.message}")