from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Rank = Literal["A", "B", "C", "D", "E", "F"]
RANK_ORDER: list[Rank] = ["A", "B", "C", "D", "E", "F"]


class ComplexityFinding(BaseModel):
    file: str
    function_name: str
    line_number: int = Field(ge=0)
    complexity_score: int = Field(ge=0)
    rank: Rank  # radon's letter grade: A (simple) through F (very complex)


def run_complexity_analysis(
    target_path: str,
    min_rank: Rank = "C",
    limit: int = 10,
) -> list[ComplexityFinding]:
    """
    Run radon's cyclomatic complexity analysis on a file or directory.

    Args:
        target_path: path to a file or directory to analyze.
        min_rank: only return findings at or above this rank.
                  radon ranks: A (1-5, simple) -> F (41+, extremely complex).
                  Default "C" surfaces moderate-or-worse complexity only.

    Returns:
        A list of ComplexityFinding, sorted worst-first.

    Raises:
        FileNotFoundError if target_path doesn't exist.
        RuntimeError if radon fails to run or its output can't be parsed.
    """
    path = Path(target_path)
    if not path.exists():
        raise FileNotFoundError(f"target_path does not exist: {target_path}")

    # radon cc -j gives JSON output; -s includes the rank letter directly.
    result = subprocess.run(
        ["radon", "cc", "-j", "-s", str(path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 and not result.stdout:
        raise RuntimeError(
            f"radon failed on {target_path}: {result.stderr.strip()}"
        )

    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"could not parse radon output for {target_path}: {e}\n"
            f"raw stdout: {result.stdout[:500]}"
        )

    min_rank_index = RANK_ORDER.index(min_rank)
    findings: list[ComplexityFinding] = []

    for file_path, items in raw.items():
        for item in items:
            rank = item.get("rank")
            if rank is None or rank not in RANK_ORDER:
                continue
            if RANK_ORDER.index(rank) < min_rank_index:
                continue

            findings.append(
                ComplexityFinding(
                    file=file_path,
                    function_name=item.get("name", "<unknown>"),
                    line_number=max(item.get("lineno", 0), 0),
                    complexity_score=max(item.get("complexity", 0), 0),
                    rank=rank,
                )
            )

    findings.sort(key=lambda f: f.complexity_score, reverse=True)
    return findings[:limit]


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = run_complexity_analysis(target)

    if not results:
        print(f"No functions at rank E or above found in {target}")
    else:
        print(f"Found {len(results)} flagged function(s):\n")
        for f in results:
            print(
                f"  [{f.rank}] {f.file}:{f.line_number} "
                f"{f.function_name} (complexity={f.complexity_score})"
            )