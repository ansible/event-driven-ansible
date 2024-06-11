"""
url_check.py.

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

async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Poll a set of URLs and send events with status."""
    urls = args.get("urls", [])
    delay = int(args.get("delay", 1))
    verify_ssl = args.get("verify_ssl", True)
    
    # Added initialization for client_error to handle cases where an exception occurs
    client_error = ""

    if not urls:
        return

    # Added url_states dictionary to track the last known status of each URL
    url_states = {url: None for url in urls}

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        async with session.get(url, ssl=verify_ssl) as resp:
                            status = "up" if resp.status == OK else "down"
                            status_code = resp.status
                    except aiohttp.ClientError as exc:
                        status = "down"
                        status_code = None
                        client_error = str(exc)
                    # Only trigger event if the status has changed
                    if url_states[url] != status:
                        url_states[url] = status
                        event = {
                            "url_check": {
                                "url": url,
                                "status": status,
                                "status_code": status_code,
                            },
                        }
                        if status == "down" and client_error:
                            event["url_check"]["error_msg"] = client_error
                        await queue.put(event)
        except Exception as exc:
            print(f"An error occurred: {exc}")

        await asyncio.sleep(delay)

if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self: "MockQueue", event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"urls": ["http://redhat.com"], "delay": 10}))
