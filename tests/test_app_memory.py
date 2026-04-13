"""Tests for app_memory — split storage load/save roundtrip."""

import json
import pytest

from gui_harness.memory import app_memory


class TestAppMemorySplitStorage:

    def test_meta_roundtrip(self, tmp_path):
        meta = {"app": "test", "detect_count": 5, "forget_threshold": 15}
        app_memory.save_meta(tmp_path, meta)
        loaded = app_memory.load_meta(tmp_path)
        assert loaded["app"] == "test"
        assert loaded["detect_count"] == 5

    def test_meta_defaults(self, tmp_path):
        """Loading from non-existent file returns sensible defaults."""
        meta = app_memory.load_meta(tmp_path)
        assert meta["detect_count"] == 0
        assert meta["forget_threshold"] == app_memory.DEFAULT_FORGET_THRESHOLD

    def test_components_roundtrip(self, tmp_path):
        comps = {
            "search_bar": {
                "type": "icon",
                "label": "search_bar",
                "seen_count": 3,
                "consecutive_misses": 0,
            },
            "close_button": {
                "type": "icon",
                "label": "close_button",
                "seen_count": 1,
                "consecutive_misses": 2,
            },
        }
        app_memory.save_components(tmp_path, comps)
        loaded = app_memory.load_components(tmp_path)
        assert "search_bar" in loaded
        assert loaded["close_button"]["consecutive_misses"] == 2

    def test_components_empty(self, tmp_path):
        assert app_memory.load_components(tmp_path) == {}

    def test_states_roundtrip(self, tmp_path):
        states = {"state_abc": {"components": ["a", "b", "c"]}}
        app_memory.save_states(tmp_path, states)
        loaded = app_memory.load_states(tmp_path)
        assert loaded["state_abc"]["components"] == ["a", "b", "c"]

    def test_states_empty(self, tmp_path):
        assert app_memory.load_states(tmp_path) == {}

    def test_transitions_roundtrip(self, tmp_path):
        trans = {
            "s1|click:btn|s2": {
                "from": "s1", "to": "s2",
                "action": "click", "target": "btn",
                "use_count": 3,
            }
        }
        app_memory.save_transitions(tmp_path, trans)
        loaded = app_memory.load_transitions(tmp_path)
        assert loaded["s1|click:btn|s2"]["use_count"] == 3

    def test_transitions_empty(self, tmp_path):
        assert app_memory.load_transitions(tmp_path) == {}


class TestGetAppDir:

    def test_creates_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        d = app_memory.get_app_dir("My App")
        assert d.exists()
        assert d.name == "my_app"
        assert (d / "components").exists()

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        d1 = app_memory.get_app_dir("firefox")
        d2 = app_memory.get_app_dir("firefox")
        assert d1 == d2
