"""

url_check.py

An ansible-events event source plugin that polls a set of URLs and sends
events with their status.

Arguments:

    urls - a list of urls to poll
    delay - the number of seconds to wait between polling

Example:

    - name: check web server
      ansible.eda.url_check:
        urls:
          - http://44.201.5.56:8000/docs
        delay: 10
"""

import asyncio
import aiohttp
from typing import Any, Dict


async def main(queue: asyncio.Queue, args: Dict[str, Any]):

    urls = args.get("urls", [])
    delay = int(args.get("delay", 1))

    if not urls:
        return

    while True:
        async with aiohttp.ClientSession() as session:
            for url in urls:
                async with session.get(url) as resp:
                    await queue.put(
                        dict(
                            url_check=dict(
                                url=url,
                                status="up" if resp.status == 200 else "down",
                                status_code=resp.status,
                            )
                        )
                    )

            await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"urls": ["http://redhat.com"]}))
