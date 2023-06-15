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


async def main(queue: asyncio.Queue, args: dict[str, Any]):
    delay = args.get("delay", 0)

    for i in range(int(args["limit"])):
        await queue.put({"i": i})
        await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"limit": 5}))
