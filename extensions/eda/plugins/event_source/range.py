"""range.py.

An ansible-rulebook event source plugin for generating events with an
increasing index i.

Arguments:
---------
    limit: The upper limit of the range of the index.

Example:
-------
    - ansible.eda.range:
        limit: 5

"""

import asyncio
from typing import Any


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Generate events with an increasing index i with a limit."""
    delay = args.get("delay", 0)

    for i in range(int(args["limit"])):
        await queue.put({"i": i})
        await asyncio.sleep(delay)


if __name__ == "__main__":
    # MockQueue if running directly

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"limit": 5}))
