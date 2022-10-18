"""
journald.py
An ansible-events event source plugin that tails systemd journald logs.

Arguments:
    match - return messages that matches this field, see https://www.freedesktop.org/software/systemd/man/systemd.journal-fields.html

Examples:
    - name: Return severity 6 messages
      ansible.eda.journald:
        match: "PRIORITY=6"

    - name: Return messages when sudo is used
      become: true
      ansible.eda.journald:
        match: "_EXE=/usr/bin/sudo"

    - name: Return all messages
      ansible.eda.journald:
        match: "ALL"
"""

import asyncio
from typing import Any, Dict
from systemd import journal


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    match = args.get("match", [])

    if not match:
        return

    journal_stream = journal.Reader()

    while True:
        journal_stream.add_match(match)
        for entry in journal_stream:
            await queue.put(entry)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"match": "PRIORITY=6"}))
