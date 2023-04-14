"""
insert_hosts_to_meta.py

An ansible-rulebook event filter that extract hosts from the event data and
insert them to the meta dict. Ansible-rulebook will limit an ansible action
running on hosts in the meta dict.

Arguments:
    host_path:      The json path inside the event data to find hosts.
                    Do nothing if the key is not present or does exist in event
    path_separator: The separator to interpret host_path. Default to "."
    host_separator: The separator to interpet host string.
                    host_path can point to a string or a list. If it is a single
                    string but contains multiple hosts, use this parameter to
                    delimits the hosts. Treat the vale as a single host if the
                    parameter is not present.

Example:
    - ansible.eda.insert_hosts_to_meta
      host_path: app.target
      path_separator: .
      host_separator: ;

"""

from typing import Any, Dict

import dpath


def main(
    event: Dict[str, Any],
    host_path: str = None,
    host_separator: str = None,
    path_separator: str = ".",
) -> Dict[str, Any]:
    if not host_path:
        return event

    try:
        hosts = dpath.get(event, host_path, path_separator)
    except KeyError:
        # does not contain host
        return event

    if isinstance(hosts, str):
        hosts = hosts.split(host_separator) if host_separator else [hosts]
    elif isinstance(hosts, list) or isinstance(hosts, tuple):
        for h in hosts:
            if not isinstance(h, str):
                raise TypeError(f"{h} is not a valid hostname")
    else:
        raise TypeError(f"{hosts} is not a valid hostname")

    if "meta" not in event:
        event["meta"] = {}
    event["meta"]["hosts"] = hosts
    return event
