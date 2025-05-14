import pathlib
from asyncio import Queue
from typing import Any, Union

import yaml
from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer

DOCUMENTATION = r"""
---
short_description: Load facts from YAML files initially and when the file changes.
description:
  - An ansible-rulebook event source plugin for loading facts from YAML files
    initially and when the file changes.
options:
  files:
    description:
      - A list of file paths pointing to YAML files.
    type: list
    elements: str
"""

EXAMPLES = r"""
- ansible.eda.file:
    files:
      - /path/to/fact.yml
"""


def send_facts(queue: Queue[Any], filename: Union[str, bytes]) -> None:
    """Send facts to the queue."""
    if isinstance(filename, bytes):
        filename = str(filename, "utf-8")
    with pathlib.Path(filename).open(encoding="utf-8") as file:
        data = yaml.safe_load(file.read())
        if data is None:
            return
        if isinstance(data, dict):
            # pylint: disable=unused-variable
            coroutine = queue.put(data)
        else:
            if not isinstance(data, list):
                msg = (
                    "Unsupported facts type, expects a list of dicts found "
                    f"{type(data)}"
                )
                raise TypeError(msg)
            if not all(bool(isinstance(item, dict)) for item in data):
                msg = f"Unsupported facts type, expects a list of dicts found {data}"
                raise TypeError(msg)
            for item in data:
                # pylint: disable=unused-variable
                coroutine = queue.put(item)  # noqa: F841


def main(queue: Queue[Any], args: dict[str, Any]) -> None:
    """Load facts from YAML files initially and when the file changes."""
    files = [pathlib.Path(f).resolve().as_posix() for f in args.get("files", [])]

    if not files:
        return

    for filename in files:
        send_facts(queue, filename)
    _observe_files(queue, files)


def _observe_files(queue: Queue[Any], files: list[str]) -> None:
    class Handler(RegexMatchingEventHandler):
        """A handler for file events."""

        def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self, event: FileSystemEvent) -> None:
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_deleted(self: "Handler", event: FileSystemEvent) -> None:
            pass

        def on_modified(self: "Handler", event: FileSystemEvent) -> None:
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_moved(self: "Handler", event: FileSystemEvent) -> None:
            pass

    observer = Observer()
    handler = Handler()

    for filename in files:
        directory = pathlib.Path(filename).parent
        observer.schedule(handler, directory.absolute().as_posix(), recursive=False)

    observer.start()

    try:
        observer.join()
    finally:
        observer.stop()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    main(MockQueue(), {"files": ["facts.yml"]})
