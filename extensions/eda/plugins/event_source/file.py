"""file.py.

An ansible-rulebook event source plugin for loading facts from YAML files
initially and when the file changes.

Arguments:
---------
    files - a list of YAML files

Example:
-------
    - ansible.eda.file:
      files:
        - fact.yml

"""

from __future__ import annotations

import pathlib

import yaml
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


def send_facts(queue, filename: str) -> None:  # noqa: ANN001
    """Send facts to the queue."""
    with pathlib.Path(filename).open(encoding="utf-8") as file:
        data = yaml.safe_load(file.read())
        if data is None:
            return
        if isinstance(data, dict):
            queue.put(data)
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
                queue.put(item)


def main(queue, args: dict) -> None:  # noqa: ANN001
    """Load facts from YAML files initially and when the file changes."""
    files = [pathlib.Path(f).resolve().as_posix() for f in args.get("files", [])]

    if not files:
        return

    for filename in files:
        send_facts(queue, filename)
    _observe_files(queue, files)


def _observe_files(queue, files: list[str]) -> None:  # noqa: ANN001
    class Handler(RegexMatchingEventHandler):
        """A handler for file events."""

        def __init__(self: Handler, **kwargs) -> None:  # noqa: ANN003
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self: Handler, event: dict) -> None:
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_deleted(self: Handler, event: dict) -> None:
            pass

        def on_modified(self: Handler, event: dict) -> None:
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_moved(self: Handler, event: dict) -> None:
            pass

    observer = Observer()
    handler = Handler()

    for filename in files:
        directory = pathlib.Path(filename).parent
        observer.schedule(handler, directory, recursive=False)

    observer.start()

    try:
        observer.join()
    finally:
        observer.stop()


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self: MockQueue, event: dict) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    main(MockQueue(), {"files": ["facts.yml"]})
