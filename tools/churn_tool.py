from __future__ import annotations

from pydantic import BaseModel, Field, computed_field

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError


# Commit messages containing any of these words (case-insensitive) are
# counted as "bugfix" commits. Heuristic, not ground truth.
BUGFIX_KEYWORDS = ["fix", "bug", "patch", "hotfix", "issue"]


class ChurnFinding(BaseModel):
    file: str
    total_commits: int = Field(ge=1)
    bugfix_commits: int = Field(ge=0)

    @computed_field
    @property
    def bugfix_rate(self) -> float:
        return round(self.bugfix_commits / self.total_commits, 3)


def run_churn_analysis(
    repo_path: str,
    max_commits: int = 500,
    min_total_commits: int = 3,
    limit: int = 10,
) -> list[ChurnFinding]:
    
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        raise FileNotFoundError(
            f"{repo_path} is not inside a git repository: {e}"
        )

    file_stats: dict[str, dict[str, int]] = {}
    commits = list(repo.iter_commits(max_count=max_commits))

    for commit in commits:
        message = commit.message.lower()
        is_bugfix = any(keyword in message for keyword in BUGFIX_KEYWORDS)

        try:
            changed_files = commit.stats.files.keys()
        except Exception:
            # Merge commits etc. can raise here; skip rather than fail.
            continue

        for file_path in changed_files:
            stats = file_stats.setdefault(
                file_path, {"total": 0, "bugfix": 0}
            )
            stats["total"] += 1
            if is_bugfix:
                stats["bugfix"] += 1

    findings: list[ChurnFinding] = []
    for file_path, stats in file_stats.items():
        if stats["total"] < min_total_commits:
            continue
        findings.append(
            ChurnFinding(
                file=file_path,
                total_commits=stats["total"],
                bugfix_commits=stats["bugfix"],
            )
        )

    findings.sort(
        key=lambda f: (f.bugfix_rate, f.total_commits), reverse=True
    )
    return findings[:limit]


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = run_churn_analysis(target)

    if not results:
        print(f"No files with >= min_total_commits found in {target}")
    else:
        print(f"Found {len(results)} file(s) with churn history:\n")
        for f in results[:20]:
            print(
                f"  {f.file}: {f.total_commits} commits, "
                f"{f.bugfix_commits} bugfixes "
                f"({f.bugfix_rate:.0%} bugfix rate)"
            )