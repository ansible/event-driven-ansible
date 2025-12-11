"""Event filter plugin for extracting hosts from event data and inserting into meta.

This module provides functionality to extract host information from event data
using JSON paths and insert them into the event's meta dictionary for limiting
action execution to specific hosts.
"""

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
    """Exception raised when the specified path does not exist in the event.

    This exception is raised when the host_path parameter points to a location
    that does not exist in the event data structure and raise_error is True.
    """


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
    """Extract hosts from event data and insert into meta dict.

    This function extracts host information from the event data using the
    specified JSON path and inserts it into the event's meta dictionary.
    The hosts can be a string, a list, or a delimited string.

    :param event: The event dictionary to process
    :type event: dict[str, Any]
    :param host_path: The JSON path to find hosts in the event data
    :type host_path: str | None
    :param host_separator: The separator to split a host string into multiple hosts
    :type host_separator: str | None
    :param path_separator: The separator to interpret the host_path
    :type path_separator: str
    :param raise_error: Whether to raise PathNotExistError if host_path does not exist
    :type raise_error: bool
    :param log_error: Whether to log an error message if host_path does not exist
    :type log_error: bool
    :returns: The modified event dictionary with hosts inserted into meta
    :rtype: dict[str, Any]
    :raises PathNotExistError: If host_path does not exist and raise_error is True
    :raises TypeError: If hosts value is not a string, list, or tuple
    """
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
