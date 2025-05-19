from __future__ import annotations

import logging
from typing import Any

import dpath

DOCUMENTATION = r"""
---
short_description: Extract hosts from the event data and insert them to the meta dict.
description:
  - An ansible-rulebook event filter that extracts hosts from the event data and
    inserts them to the meta dict. In ansible-rulebook, this will limit an action
    running on hosts in the meta dict.
options:
  host_path:
    description:
      - The json path inside the event data to find hosts.
      - Do nothing if the key is not present or does exist in event.
    type: str
    default: null
  path_separator:
    description:
      - The separator to interpret host_path.
    type: str
    default: "."
  host_separator:
    description:
      - The separator to interpret host string.
      - host_path can point to a string or a list. If it is a single
        string but contains multiple hosts, use this parameter to
        delimits the hosts. Treat the value as a single host if the
        parameter is not present.
    type: str
    default: null
  raise_error:
    description:
      - Whether raise PathNotExistError if host_path does not
        exist in the event.
      - It is recommended to turn it on during the rulebook
        development time. You can then turn it off for production.
    type: bool
    default: false
  log_error:
    description:
      - Whether log an error message if host_path does not
        exist in the event.
      - You can turn if off if it is expected to have events not
        having the host_path to avoid noises in the log.
    type: bool
    default: true
"""

EXAMPLES = r"""
- ansible.eda.alertmanager:
    host: 0.0.0.0
    port: 5050
  filters:
    - ansible.eda.insert_hosts_to_meta:
        host_path: "app.target"
        path_separator: "."
        host_separator: ";"
        raise_error: true
        log_error: true
"""

LOGGER = logging.getLogger(__name__)


class PathNotExistError(Exception):
    """Cannot find the path in the event."""


# pylint: disable=too-many-arguments
def main(
    event: dict[str, Any],
    host_path: str | None = None,
    host_separator: str | None = None,
    path_separator: str = ".",
    *,
    raise_error: bool = False,
    log_error: bool = True,
) -> dict[str, Any]:
    """Extract hosts from event data and insert into meta dict."""
    if not host_path:
        return event

    try:
        hosts = dpath.get(event, host_path, path_separator)
    except KeyError as error:
        # does not contain host
        msg = f"Event {event} does not contain {host_path}"
        if log_error:
            LOGGER.error(msg)  # noqa: TRY400
        if raise_error:
            raise PathNotExistError(msg) from error
        return event

    if isinstance(hosts, str):
        hosts = hosts.split(host_separator) if host_separator else [hosts]
    elif isinstance(hosts, (list, tuple)):
        for host in hosts:
            if not isinstance(host, str):
                msg = f"{host} is not a valid hostname"
                raise TypeError(msg)
    else:
        msg = f"{hosts} is not a valid hostname"
        raise TypeError(msg)

    if "meta" not in event:
        event["meta"] = {}
    event["meta"]["hosts"] = hosts
    return event
