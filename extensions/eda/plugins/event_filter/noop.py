from typing import Any

DOCUMENTATION = r"""
---
author:
  - Doston Toirov (@dtoirov)
short_description: Do nothing.
description:
  - An event filter that does nothing to the input.
"""


def main(event: dict[str, Any]) -> dict[str, Any]:
    """Return the input."""
    return event
