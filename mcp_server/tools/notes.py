"""In-memory note storage for the Sage MCP server."""

_notes: dict[str, str] = {}


def save_note(key: str, content: str) -> str:
    """
    Store content under a key in the in-memory notes dict.

    Overwrites existing content if the key already exists.
    """
    if not key or not key.strip():
        raise ValueError("key must be a non-empty string")
    if content is None:
        raise ValueError("content must not be None")

    normalized_key = key.strip()
    _notes[normalized_key] = content
    return f"Note saved under key '{normalized_key}' ({len(content)} characters)."


def get_note(key: str) -> str | None:
    """Retrieve a note by key, or None if not found."""
    return _notes.get(key.strip() if key else "")


def clear_notes() -> None:
    """Clear all stored notes. Intended for testing."""
    _notes.clear()


def list_note_keys() -> list[str]:
    """Return all stored note keys."""
    return list(_notes.keys())
