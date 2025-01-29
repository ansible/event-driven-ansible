from __future__ import annotations

import logging
from typing import Any

import dpath

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
    elif isinstance(hosts, (list, tuple)):  # noqa: UP038
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
