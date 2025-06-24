from __future__ import annotations

import fnmatch
from typing import Any, Optional

DOCUMENTATION = r"""
---
short_description: Filter keys out of events.
description:
  - An event filter that filters keys out of events.
    Includes override excludes.
    This is useful to exclude information from events that is unneeded by the rule engine.
options:
  exclude_keys:
    description:
      - A list of strings or patterns to remove.
    type: list
    elements: str
    default: null
  include_keys:
    description:
      - A list of strings or patterns to keep even if it matches exclude_keys patterns.
    type: list
    elements: str
    default: null
notes:
  - The values in both parameters - include_keys and exclude_keys, must be a full path in
    top to bottom order to the keys to be filtered (or left to right order if it is given
    as a list), as shown in the examples below.
"""

EXAMPLES = r"""
- ansible.eda.generic:
    payload:
      key1:
        key2:
          f_ignore_1: 1
          f_ignore_2: 2
      key3:
        key4:
          f_use_1: 42
          f_use_2: 45
  filters:
    - ansible.eda.json_filter:
        include_keys:
          - key3
          - key4
          - f_use*
        exclude_keys: ['key1', 'key2', 'f_ignore_1']
"""


def _matches_include_keys(include_keys: list[str], string: str) -> bool:
    return any(fnmatch.fnmatch(string, pattern) for pattern in include_keys)


def _matches_exclude_keys(exclude_keys: list[str], string: str) -> bool:
    return any(fnmatch.fnmatch(string, pattern) for pattern in exclude_keys)


def main(
    event: dict[str, Any],
    exclude_keys: Optional[list[str]] = None,  # noqa: UP045
    include_keys: Optional[list[str]] = None,  # noqa: UP045
) -> dict[str, Any]:
    """Filter keys out of events."""
    if exclude_keys is None:
        exclude_keys = []

    if include_keys is None:
        include_keys = []

    queue = []
    queue.append(event)
    while queue:
        obj = queue.pop()
        if isinstance(obj, dict):
            for item in list(obj.keys()):
                if (item in include_keys) or _matches_include_keys(include_keys, item):
                    queue.append(obj[item])
                elif (item in exclude_keys) or _matches_exclude_keys(
                    exclude_keys,
                    item,
                ):
                    del obj[item]
                else:
                    queue.append(obj[item])

    return event
