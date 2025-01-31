import asyncio
import itertools
from typing import Any

DOCUMENTATION = r"""
---
author:
  - Doston Toirov (@dtoirov)
short_description: Generate events with an increasing index i that never ends.
description:
  - An ansible-rulebook event source plugin for generating events with an increasing index i that never ends.
version_added: '2.4.0'
options:
  delay:
    description:
      - Time between ticks.
    type: int
"""

EXAMPLES = r"""
- ansible.eda.tick:
    delay: 5
"""


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Generate events with an increasing index i and a time between ticks."""
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
