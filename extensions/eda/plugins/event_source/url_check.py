import asyncio
from typing import Any

import aiohttp

DOCUMENTATION = r"""
---
short_description: Poll a set of URLs and sends events with their status.
description:
  - An ansible-rulebook event source plugin that polls a set of URLs and sends events with their status.
options:
  urls:
    description:
      - A list of urls to poll.
    type: list
    elements: str
    required: true
  delay:
    description:
      - The delay (in seconds) between polling.
    type: int
    default: 1
  verify_ssl:
    description:
      - Verify SSL certificate.
    type: bool
    default: true
"""

EXAMPLES = r"""
- ansible.eda.url_check:
    urls:
      - http://44.201.5.56:8000/docs
    delay: 10
"""

OK = 200


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Poll a set of URLs and send events with status."""
    urls = args.get("urls", [])
    delay = int(args.get("delay", 1))
    verify_ssl = args.get("verify_ssl", True)

    if not urls:
        return

    while True:
        for url in urls:
            try:
                async with aiohttp.ClientSession() as session:  # noqa: SIM117
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

            except aiohttp.ClientError as exc:  # noqa: PERF203
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
