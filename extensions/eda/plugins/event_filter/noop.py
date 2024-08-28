"""noop.py:   An event filter that does nothing to the input."""

from typing import Any


def main(event: dict[str, Any]) -> dict[str, Any]:
    """Return the input."""
    return event
