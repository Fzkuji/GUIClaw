"""Tests for parse_json — delegates to agentic.functions._utils.parse_json."""

import pytest

from gui_harness.utils import parse_json


class TestParseJson:

    def test_direct_json(self):
        assert parse_json('{"key": "value"}') == {"key": "value"}

    def test_markdown_fence(self):
        text = 'Here is the result:\n```json\n{"score": 8}\n```\nDone.'
        assert parse_json(text) == {"score": 8}

    def test_bare_json_in_text(self):
        text = 'The output is {"status": "ok", "count": 3} as expected.'
        result = parse_json(text)
        assert result["status"] == "ok"
        assert result["count"] == 3

    def test_nested_json(self):
        text = 'Result: {"data": {"nested": true}, "list": [1, 2]}'
        result = parse_json(text)
        assert result["data"]["nested"] is True

    def test_no_json_raises(self):
        with pytest.raises((ValueError, Exception)):
            parse_json("no json here at all")

    def test_action_json(self):
        text = '```json\n{"call": "click", "args": {"target": "OK button"}}\n```'
        result = parse_json(text)
        assert result["call"] == "click"
        assert result["args"]["target"] == "OK button"
