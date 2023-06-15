"""url_check.py.

An ansible-rulebook event source plugin that polls a set of URLs and sends
events with their status.

Arguments:
---------
    urls - a list of urls to poll
    delay - the number of seconds to wait between polling
    verify_ssl - verify SSL certificate

Example:
-------
    - name: check web server
      ansible.eda.url_check:
        urls:
          - http://44.201.5.56:8000/docs
        delay: 10

"""

import asyncio
from typing import Any

import aiohttp


async def main(queue: asyncio.Queue, args: dict[str, Any]):
    urls = args.get("urls", [])
    delay = int(args.get("delay", 1))
    verify_ssl = args.get("verify_ssl", True)

    if not urls:
        return

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    async with session.get(url, verify_ssl=verify_ssl) as resp:
                        await queue.put(
                            {
                                "url_check": {
                                    "url": url,
                                    "status": "up" if resp.status == 200 else "down",
                                    "status_code": resp.status,
                                },
                            },
                        )

        except aiohttp.ClientError as e:
            client_error = str(e)
            await queue.put(
                {
                    "url_check": {
                        "url": url,
                        "status": "down",
                        "error_msg": client_error,
                    },
                },
            )

        await asyncio.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"urls": ["http://redhat.com"]}))
