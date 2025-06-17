import asyncio
from typing import Any

# https://github.com/pylint-dev/pylint/issues/7240
# Also systemd-python fails to install on pre-commit.ci due to:
# No such file or directory: 'pkg-config'
# pylint: disable=import-error
from systemd import journal  # type: ignore # noqa: PGH003

DOCUMENTATION = r"""
---
short_description: Tail systemd journald logs.
description:
  - An ansible-rulebook event source plugin that tails systemd journald logs.
options:
  match:
    description:
      - A string used to match messages and return them, see
        https://www.freedesktop.org/software/systemd/man/systemd.journal-fields.html.
    type: str
    required: true
  delay:
    description:
      - The delay (in seconds) between messages.
    type: int
    default: 0
"""

EXAMPLES = r"""
- name: Return severity 6 messages
  ansible.eda.journald:
    match: "PRIORITY=6"

- name: Return messages when sudo is used
  ansible.eda.journald:
    match: "_EXE=/usr/bin/sudo"

- name: Return all messages
  ansible.eda.journald:
    match: "ALL"
"""


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Read journal entries and add them to the provided queue.

    Args:
    ----
        queue (asyncio.Queue): The queue to which journal entries will be added.
        args (dict[str, Any]): Additional arguments:
            - delay (int): The delay in seconds. Defaults to 0.
            - match (str): A string to match.

    Returns:
    -------
        None

    """
    delay = args.get("delay", 0)
    match = args.get("match", [])

    if not match:
        return

    journal_stream = journal.Reader()
    journal_stream.seek_tail()

    while True:
        if match != "ALL":
            journal_stream.add_match(match)
        for entry in journal_stream:
            stream_dict = {}
            for field in entry:
                stream_dict[field.lower()] = f"{entry[field]}"

            await queue.put({"journald": stream_dict})
            await asyncio.sleep(delay)

            stream_dict.clear()


if __name__ == "__main__":
    """
    Entry point of the program.
    """

    class MockQueue(asyncio.Queue[Any]):
        """A mock implementation of a queue that prints the event."""

        async def put(self, event: str) -> None:
            """Add the event to the queue and print it."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"match": "ALL"}))
