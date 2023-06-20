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

import fnmatch


def _matches_include_keys(include_keys: list, s: str) -> bool:
    return any(fnmatch.fnmatch(s, pattern) for pattern in include_keys)


def _matches_exclude_keys(exclude_keys: list, s: str) -> bool:
    return any(fnmatch.fnmatch(s, pattern) for pattern in exclude_keys)


def main(event: dict, exclude_keys: list = None, include_keys: list = None) -> dict:
    """Filter keys out of events."""
    if exclude_keys is None:
        exclude_keys = []

    if include_keys is None:
        include_keys = []

    q = []
    q.append(event)
    while q:
        o = q.pop()
        if isinstance(o, dict):
            for i in list(o.keys()):
                if (i in include_keys) or _matches_include_keys(include_keys, i):
                    q.append(o[i])
                elif (i in exclude_keys) or _matches_exclude_keys(exclude_keys, i):
                    del o[i]
                else:
                    q.append(o[i])

    return event
