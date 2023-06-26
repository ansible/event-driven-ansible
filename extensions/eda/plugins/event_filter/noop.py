"""noop.py:   An event filter that does nothing to the input."""


def main(event: dict) -> dict:
    """Return the input."""
    return event
