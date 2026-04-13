"""Tests for component_memory — activity tracking and state transitions."""

import json
import pytest

from gui_harness.memory import app_memory
from gui_harness.planning.component_memory import (
    _update_activity,
    identify_state,
    record_transition,
    get_available_transitions,
    FORGET_THRESHOLD,
)


class TestUpdateActivity:

    def _setup_components(self, tmp_path):
        """Create a test app dir with some components."""
        comps = {
            "search_bar": {
                "type": "icon", "label": "search_bar",
                "icon_file": "components/search_bar.png",
                "seen_count": 5, "consecutive_misses": 0,
            },
            "close_button": {
                "type": "icon", "label": "close_button",
                "icon_file": "components/close_button.png",
                "seen_count": 2, "consecutive_misses": FORGET_THRESHOLD - 1,
            },
        }
        app_memory.save_components(tmp_path, comps)
        # Create dummy icon files
        comp_dir = tmp_path / "components"
        comp_dir.mkdir(exist_ok=True)
        (comp_dir / "search_bar.png").write_text("dummy")
        (comp_dir / "close_button.png").write_text("dummy")
        return comps

    def test_matched_component_resets_misses(self, tmp_path):
        self._setup_components(tmp_path)
        _update_activity(tmp_path, {"search_bar"})
        loaded = app_memory.load_components(tmp_path)
        assert loaded["search_bar"]["seen_count"] == 6
        assert loaded["search_bar"]["consecutive_misses"] == 0

    def test_unmatched_component_increments_misses(self, tmp_path):
        """Component at threshold - 2 should increment but not be deleted."""
        comps = {
            "search_bar": {
                "type": "icon", "label": "search_bar",
                "icon_file": "components/search_bar.png",
                "seen_count": 5, "consecutive_misses": 0,
            },
            "close_button": {
                "type": "icon", "label": "close_button",
                "icon_file": "components/close_button.png",
                "seen_count": 2, "consecutive_misses": FORGET_THRESHOLD - 2,
            },
        }
        app_memory.save_components(tmp_path, comps)
        comp_dir = tmp_path / "components"
        comp_dir.mkdir(exist_ok=True)
        (comp_dir / "close_button.png").write_text("dummy")

        _update_activity(tmp_path, {"search_bar"})
        loaded = app_memory.load_components(tmp_path)
        assert loaded["close_button"]["consecutive_misses"] == FORGET_THRESHOLD - 1

    def test_stale_component_deleted(self, tmp_path):
        self._setup_components(tmp_path)
        # close_button is at FORGET_THRESHOLD - 1, one more miss triggers deletion
        _update_activity(tmp_path, {"search_bar"})
        loaded = app_memory.load_components(tmp_path)
        assert "close_button" not in loaded
        assert not (tmp_path / "components" / "close_button.png").exists()

    def test_empty_components_noop(self, tmp_path):
        app_memory.save_components(tmp_path, {})
        _update_activity(tmp_path, set())


class TestRecordTransition:

    def test_records_transition(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        app_dir = app_memory.get_app_dir("test_app")
        record_transition("test_app", "state_a", "click", "ok_button", "state_b")
        trans = app_memory.load_transitions(app_dir)
        key = "state_a|click:ok_button"
        assert key in trans
        assert trans[key]["to"] == "state_b"

    def test_skips_none_states(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        app_dir = app_memory.get_app_dir("test_app")
        record_transition("test_app", None, "click", "btn", "state_b")
        assert app_memory.load_transitions(app_dir) == {}

    def test_increments_use_count(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        app_dir = app_memory.get_app_dir("test_app")
        record_transition("test_app", "a", "click", "btn", "b")
        record_transition("test_app", "a", "click", "btn", "b")
        trans = app_memory.load_transitions(app_dir)
        assert trans["a|click:btn"]["use_count"] == 2


class TestGetAvailableTransitions:

    def test_returns_transitions(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_memory, "MEMORY_DIR", tmp_path)
        app_dir = app_memory.get_app_dir("test_app")
        record_transition("test_app", "home", "click", "settings_icon", "settings")
        record_transition("test_app", "home", "click", "search_bar", "search")
        available = get_available_transitions("test_app", "home")
        assert len(available) == 2
        targets = {t["target"] for t in available}
        assert "settings_icon" in targets
        assert "search_bar" in targets

    def test_none_state_returns_empty(self):
        assert get_available_transitions("any_app", None) == []
