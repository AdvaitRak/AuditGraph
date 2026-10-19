from __future__ import annotations

import json
from dataclasses import dataclass

FINISH = "finish"


class ParseError(Exception):
    """The LLM's reply couldn't be understood. The message is shown back to the LLM."""


@dataclass(frozen=True)
class Step:
    thought: str
    action: str   # a tool name, or "finish"
    args: dict


def parse_step(reply: str) -> Step:
    """Turn the LLM's text reply into a Step, or raise ParseError."""
    # Models often add chatter or ```json fences around the JSON, so take
    # everything from the first "{" to the last "}".
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        raise ParseError("no JSON object found in your reply")

    try:
        # strict=False allows raw newlines inside strings, which models
        # often produce when they put multi-line code in "old_text"/"new_text".
        data = json.loads(reply[start : end + 1], strict=False)
    except json.JSONDecodeError as e:
        raise ParseError(
            f"your reply is not valid JSON ({e.msg}, line {e.lineno}, column {e.colno})"
        ) from e

    if not isinstance(data, dict):
        raise ParseError("your reply must be a single JSON object")

    action = data.get("action")
    if not isinstance(action, str) or not action.strip():
        raise ParseError('missing "action" (a tool name, or "finish")')

    args = data.get("args", {})
    if not isinstance(args, dict):
        raise ParseError('"args" must be a JSON object, like {"path": "a.py"}')

    return Step(
        thought=str(data.get("thought", "")).strip(),
        action=action.strip(),
        args=args,
    )