import logging
import multiprocessing as mp
import re
from typing import Any

normalize_regex = re.compile("[^0-9a-zA-Z_]+")


def main(
    event: dict[str, Any], overwrite: bool = True
) -> dict[str, Any]:  # noqa: FBT001, FBT002
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
