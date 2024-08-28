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

OK = 200


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Poll a set of URLs and send events with status."""
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
                                    "status": "up" if resp.status == OK else "down",
                                    "status_code": resp.status,
                                },
                            },
                        )

        except aiohttp.ClientError as exc:
            client_error = str(exc)
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
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"urls": ["http://redhat.com"]}))
