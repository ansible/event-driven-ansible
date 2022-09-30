"""
range.py

An ansible-events event source plugin for generating events with an increasing index i.

Arguments:
    limit: The upper limit of the range of the index.

Example:

    - ansible.eda.range:
        limit: 5

"""

import asyncio
from typing import Any, Dict


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    delay = args.get("delay", 0)

    for i in range(int(args["limit"])):
        await queue.put(dict(i=i))
        await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), dict(limit=5)))
