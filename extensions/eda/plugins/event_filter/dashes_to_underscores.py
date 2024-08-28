"""dashes_to_underscores.py.

    An event filter that changes dashes in keys to underscores.
    For instance, the key X-Y becomes the new key X_Y.

Arguments:
---------
    * overwrite: Overwrite the values if there is a collision with a new key.

"""

import multiprocessing as mp
from typing import Any


def main(
    event: dict[str, Any], overwrite: bool = True
) -> dict[str, Any]:  # noqa: FBT001, FBT002
    """Change dashes in keys to underscores."""
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
