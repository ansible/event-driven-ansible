"""insert_hosts_to_meta.py.

An ansible-rulebook event filter that extract hosts from the event data and
insert them to the meta dict. Ansible-rulebook will limit an ansible action
running on hosts in the meta dict.

Arguments:
---------
    host_path:      The json path inside the event data to find hosts.
                    Do nothing if the key is not present or does exist in event
    path_separator: The separator to interpret host_path. Default to "."
    host_separator: The separator to interpet host string.
                    host_path can point to a string or a list. If it is a single
                    string but contains multiple hosts, use this parameter to
                    delimits the hosts. Treat the vale as a single host if the
                    parameter is not present.

Example:
-------
    - ansible.eda.insert_hosts_to_meta
      host_path: app.target
      path_separator: .
      host_separator: ;

"""

from typing import Any

import dpath


def main(
    event: dict[str, Any],
    host_path: str = None,
    host_separator: str = None,
    path_separator: str = ".",
) -> dict[str, Any]:
    """Extract hosts from event data and insert into meta dict."""
    if not host_path:
        return event

    try:
        hosts = dpath.get(event, host_path, path_separator)
    except KeyError:
        # does not contain host
        return event

    if isinstance(hosts, str):
        hosts = hosts.split(host_separator) if host_separator else [hosts]
    elif isinstance(hosts, list | tuple):
        for h in hosts:
            if not isinstance(h, str):
                msg = f"{h} is not a valid hostname"
                raise TypeError(msg)
    else:
        msg = f"{hosts} is not a valid hostname"
        raise TypeError(msg)

    if "meta" not in event:
        event["meta"] = {}
    event["meta"]["hosts"] = hosts
    return event
