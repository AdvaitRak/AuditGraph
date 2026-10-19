from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from config.settings import load_settings
from tools.edit_tool import edit_file
from tools.file_tools import list_files, read_file, search_code
from tools.verify_tools import check_complexity, check_syntax, run_lint


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: dict[str, str]          
    run: Callable[..., str]       


TOOLS: dict[str, Tool] = {
    t.name: t
    for t in [
        Tool(
            "list_files",
            "List the files and folders inside a folder of the repo.",
            {"directory": "folder path, default '.' (optional)"},
            list_files,
        ),
        Tool(
            "read_file",
            "Read a .py file with line numbers. Long files come in pages.",
            {
                "path": "file path inside the repo",
                "start_line": "first line to read (optional)",
                "end_line": "last line to read (optional)",
            },
            read_file,
        ),
        Tool(
            "search_code",
            "Search all .py files for a regex or plain text. Shows file:line: text.",
            {"pattern": "text or regex to find", "directory": "where to search (optional)"},
            search_code,
        ),
        Tool(
            "edit_file",
            "Replace ONE exact piece of text in a .py file. A human must approve it. "
            "Cannot edit test files or change function signatures.",
            {
                "path": "file path inside the repo",
                "old_text": "exact text to replace (copy it from read_file, WITHOUT line numbers)",
                "new_text": "the replacement text",
            },
            edit_file,
        ),
        Tool(
            "check_syntax",
            "Check that a .py file is still valid Python.",
            {"path": "file path inside the repo"},
            check_syntax,
        ),
        Tool(
            "check_complexity",
            "List functions in a .py file that are still complex (radon rank C or worse).",
            {"path": "file path inside the repo"},
            check_complexity,
        ),
        Tool(
            "run_lint",
            "Run the linter on a .py file (bugs, unused imports, undefined names).",
            {"path": "file path inside the repo"},
            run_lint,
        ),
    ]
}


def describe_tools() -> str:
    """The tool list as text, to put inside the LLM prompt."""
    lines = []
    for tool in TOOLS.values():
        args = ", ".join(f"{name}: {meaning}" for name, meaning in tool.args.items())
        lines.append(f"- {tool.name}({args})\n    {tool.description}")
    return "\n".join(lines)


def execute_tool(repo_root: str, name: str, args: dict) -> str:
    """Run one tool and ALWAYS return text. Errors become text the LLM can read."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"Error: unknown tool '{name}'. Available tools: {', '.join(TOOLS)}"
    if not isinstance(args, dict):
        return "Error: args must be a JSON object"

    try:
        result = tool.run(repo_root, **args)
    except TypeError as e:
        return f"Error: wrong arguments for {name}: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    limit = load_settings().max_observation_chars
    if len(result) > limit:
        result = result[:limit] + f"\n... [output cut at {limit} characters]"
    return result