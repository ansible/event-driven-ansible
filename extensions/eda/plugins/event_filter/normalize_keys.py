import logging
import multiprocessing as mp
import re
from typing import Any

DOCUMENTATION = r"""
---
short_description: Change keys that contain non-alpha numeric or underscore to underscores.
description: |
  - An event filter that changes keys that contain non alpha numeric or
    underscore to underscores.
  - For instance, the key server-name becomes the new key server_name.
    If there are consecutive non alpha numeric or under score, they would
    be coalesced into a single underscore.
    For instance the key server.com/&abc becomes server_com_abc
    instead of server_com__abc.
  - If there is a existing key with the normalized name, it will get overwritten
    by default. If you don't want to over write it you can pass in "overwrite: false"
    The default value of overwrite is true.
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
    ansible.eda.normalize_keys:

- ansible.eda.alertmanager:
    host: 0.0.0.0
    port: 5050
  filters:
    ansible.eda.normalize_keys:
      overwrite: false
"""

normalize_regex = re.compile("[^0-9a-zA-Z_]+")


def main(
    event: dict[str, Any],
    overwrite: bool = True,  # noqa: FBT001, FBT002
) -> dict[str, Any]:
    """Change keys that contain non-alphanumeric characters to underscores."""
    logger = mp.get_logger()
    logger.info("normalize_keys")
    return _normalize_embedded_keys(event, overwrite, logger)


def _normalize_embedded_keys(
    obj: dict[str, Any],
    overwrite: bool,  # noqa: FBT001
    logger: logging.Logger,
) -> dict[str, Any]:
    if isinstance(obj, dict):
        new_dict = {}
        original_keys = list(obj.keys())
        for key in original_keys:
            new_key = normalize_regex.sub("_", key)
            if new_key == key or new_key not in original_keys:
                new_dict[new_key] = _normalize_embedded_keys(
                    obj[key],
                    overwrite,
                    logger,
                )
            elif new_key in original_keys and overwrite:
                new_dict[new_key] = _normalize_embedded_keys(
                    obj[key],
                    overwrite,
                    logger,
                )
                logger.warning("Replacing existing key %s", new_key)
        return new_dict
    if isinstance(obj, list):
        return [_normalize_embedded_keys(item, overwrite, logger) for item in obj]
    return obj
