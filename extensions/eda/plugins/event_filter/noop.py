"""Event filter plugin that performs no operations.

This module provides a no-operation filter that returns the input event
unchanged. It can be used for testing or as a placeholder.
"""

from typing import Any

DOCUMENTATION = r"""
---
short_description: Do nothing.
description:
  - An event filter that does nothing to the input.
"""


def main(event: dict[str, Any]) -> dict[str, Any]:
    """Return the input event unchanged.

    This is a no-operation filter that passes through the event without
    any modifications.

    :param event: The event dictionary to process
    :returns: The same event dictionary without modifications
    """
    return event
