"""Event source plugin for generating infinite events with increasing index.

This module provides an event source plugin that generates events with an
increasing index that never ends, similar to a ticker.
"""

import asyncio
import itertools
from typing import Any

DOCUMENTATION = r"""
---
short_description: Generate events with an increasing index i that never ends.
description:
  - An ansible-rulebook event source plugin for generating events with an increasing index i that never ends.
options:
  delay:
    description:
      - The delay (in seconds) between ticks.
    type: int
    default: 1
"""

EXAMPLES = r"""
- ansible.eda.tick:
    delay: 5
"""


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Generate events with an increasing index i and a time between ticks.

    Main entry point for the tick event source plugin. Generates events with
    an infinite increasing counter starting from 1.

    :param queue: The asyncio queue to put events into
    :type queue: asyncio.Queue[Any]
    :param args: Configuration arguments including delay between ticks
    :type args: dict[str, Any]
    :returns: None
    :rtype: None
    """
    delay = args.get("delay", 1)

    for i in itertools.count(start=1):
        await queue.put({"i": i})
        await asyncio.sleep(delay)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"delay": 1}))
