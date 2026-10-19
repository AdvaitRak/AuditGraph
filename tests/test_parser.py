import pytest

from react.parser import ParseError, parse_step


def test_plain_json():
    step = parse_step('{"thought": "look", "action": "read_file", "args": {"path": "a.py"}}')
    assert step.action == "read_file"
    assert step.args == {"path": "a.py"}
    assert step.thought == "look"


def test_json_inside_code_fence_with_extra_text():
    reply = 'Sure!\n```json\n{"thought": "t", "action": "finish", "args": {"summary": "done"}}\n```'
    assert parse_step(reply).action == "finish"


def test_raw_newlines_inside_strings_are_accepted():
    reply = '{"thought": "t", "action": "edit_file", "args": {"path": "a.py", "old_text": "x = 1\n", "new_text": "x = 2\n"}}'
    assert parse_step(reply).args["new_text"] == "x = 2\n"


def test_not_json_raises():
    with pytest.raises(ParseError):
        parse_step("I think we should read the file")


def test_missing_action_raises():
    with pytest.raises(ParseError):
        parse_step('{"thought": "hmm"}')


def test_args_must_be_an_object():
    with pytest.raises(ParseError):
        parse_step('{"action": "read_file", "args": "a.py"}')