"""json_filter.py:   An event filter that filters keys out of events.

Includes override excludes.

This is useful to exclude information from events that is unneeded by the rule
engine.

Arguments:
---------
    * exclude_keys = a list of strings or patterns to remove
    * include_keys = a list of strings or patterns to keep even if it matches
    exclude_keys patterns.

"""

from __future__ import annotations

import fnmatch
from typing import Any, Optional


def _matches_include_keys(include_keys: list[str], string: str) -> bool:
    return any(fnmatch.fnmatch(string, pattern) for pattern in include_keys)


def _matches_exclude_keys(exclude_keys: list[str], string: str) -> bool:
    return any(fnmatch.fnmatch(string, pattern) for pattern in exclude_keys)


def main(
    event: dict[str, Any],
    exclude_keys: Optional[list[str]] = None,
    include_keys: Optional[list[str]] = None,
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
