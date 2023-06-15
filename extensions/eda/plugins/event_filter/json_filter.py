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


def matches_include_keys(include_keys, s):
    return any(fnmatch.fnmatch(s, pattern) for pattern in include_keys)


def matches_exclude_keys(exclude_keys, s):
    return any(fnmatch.fnmatch(s, pattern) for pattern in exclude_keys)


def main(event, exclude_keys=None, include_keys=None):
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
                if i in include_keys:
                    q.append(o[i])
                elif matches_include_keys(include_keys, i):
                    q.append(o[i])
                elif i in exclude_keys:
                    del o[i]
                elif matches_exclude_keys(exclude_keys, i):
                    del o[i]
                else:
                    q.append(o[i])

    return event
