"""Tests for mcp_server.tools.notes."""

import pytest

from mcp_server.tools.notes import clear_notes, get_note, list_note_keys, save_note


@pytest.fixture(autouse=True)
def _reset_notes():
    clear_notes()
    yield
    clear_notes()


class TestSaveNoteTool:
    def test_stores_content(self):
        message = save_note("research-1", "Finding A")

        assert "research-1" in message
        assert get_note("research-1") == "Finding A"

    def test_raises_on_empty_key(self):
        with pytest.raises(ValueError, match="non-empty"):
            save_note("", "content")

    def test_raises_on_none_content(self):
        with pytest.raises(ValueError, match="None"):
            save_note("key", None)  # type: ignore[arg-type]

    def test_lists_keys_after_save(self):
        save_note("a", "one")
        save_note("b", "two")
        assert sorted(list_note_keys()) == ["a", "b"]
