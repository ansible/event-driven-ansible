"""
dashes_to_underscores.py:   An event filter that changes dashes in keys to underscores.

For instance, the key X-Y becomes the new key X_Y.

Arguments:
    * overwrite: Overwrite the values if there is a collision with a new key.
"""

import multiprocessing as mp


def main(event, overwrite=True):
    logger = mp.get_logger()
    logger.info('dashes_to_underscores')
    q = []
    q.append(event)
    while q:
        o = q.pop()
        if isinstance(o, dict):
            for key in list(o.keys()):
                value = o[key]
                q.append(value)
                if "-" in key:
                    new_key = key.replace("-", "_")
                    del o[key]
                    if new_key in o and overwrite:
                        o[new_key] = value
                        logger.info(f'Replacing {key} with {new_key}')
                    elif new_key not in o:
                        o[new_key] = value
                        logger.info(f'Replacing {key} with {new_key}')

    return event
