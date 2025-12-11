"""Event filter plugin for converting dashes to underscores in event keys.

This module provides functionality to transform dictionary keys by replacing
dashes with underscores throughout the event data structure.
"""

import multiprocessing as mp
from typing import Any

DOCUMENTATION = r"""
---
short_description: Change dashes to underscores.
description:
  - An event filter that changes dashes in keys to underscores. For instance, the key X-Y becomes the new key X_Y.
options:
  overwrite:
    description:
      - Overwrite the values if there is a collision with a new key.
    type: bool
    default: true
"""

EXAMPLES = r"""
- ansible.eda.alertmanager:
    host: 0.0.0.0
    port: 5050
  filters:
    - ansible.eda.dashes_to_underscores:
        overwrite: false
"""


def main(
    event: dict[str, Any],
    overwrite: bool = True,  # noqa: FBT001, FBT002
) -> dict[str, Any]:
    """Change dashes in keys to underscores.

    Recursively processes the event dictionary and replaces all dashes
    in keys with underscores. Handles nested dictionaries by traversing
    the entire structure.

    :param event: The event dictionary to process
    :param overwrite: Whether to overwrite existing keys if there is a collision
                      with the new underscore-based key name
    :returns: The modified event dictionary with dashes replaced by underscores
    """
    logger = mp.get_logger()
    logger.info("dashes_to_underscores")
    queue = [event]
    while queue:
        obj = queue.pop()
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                value = obj[key]
                queue.append(value)
                if "-" in key:
                    new_key = key.replace("-", "_")
                    del obj[key]
                    if (new_key in obj and overwrite) or (new_key not in obj):
                        obj[new_key] = value
                        logger.info("Replacing %s with %s", key, new_key)

    return event
