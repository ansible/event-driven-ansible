"""
tick.py

An ansible-rulebook event source plugin for generating events with an increasing index
i that never ends.

Arguments:
    delay: time between ticks

Example:

    - ansible.eda.tick:
        delay: 5

"""
import asyncio
import itertools
from typing import Any, Dict


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    delay = args.get("delay", 1)

    for i in itertools.count(start=1):
        await queue.put(dict(i=i))
        await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), dict(delay=1)))
