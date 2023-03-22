"""
insert_source_info.py

An ansible-rulebook event filter that sets the source name and type
in the event meta field. A source name is needed to track where the
event originated from. If the event meta already has a source.name
or source.type field specified it will be ignored. This filter is
automatically added to every source.

Arguments:
          source_name
          source_type
Example:
    - ansible.eda.insert_source_info

"""

from typing import Any, Dict


def main(
    event: Dict[str, Any],
    source_name: str,
    source_type: str,
) -> Dict[str, Any]:
    if "meta" not in event:
        event["meta"] = {}

    if "source" not in event["meta"]:
        event["meta"]["source"] = {}

    if "name" not in event["meta"]["source"]:
        event["meta"]["source"]["name"] = source_name

    if "type" not in event["meta"]["source"]:
        event["meta"]["source"]["type"] = source_type

    return event
