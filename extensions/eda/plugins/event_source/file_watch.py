r"""file_watch.py.

An ansible-rulebook event source plugin for watching file system changes.

Arguments:
---------
    path: The directory to watch for changes.
    ignore_regexes: A list of regular expressions to ignore changes
    recursive: Recursively watch the path if true

Example:
-------
    - name: file_watch
      file_watch:
        path: "{{src_path}}"
        recursive: true
        ignore_regexes: ['.*\\.pytest.*', '.*__pycache__.*', '.*/.git.*']

"""

import asyncio
import concurrent.futures
from typing import Any

from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer


def watch(
    loop: asyncio.events.AbstractEventLoop,
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Watch for changes and put events on the queue."""
    root_path = args["path"]

    class Handler(RegexMatchingEventHandler):
        """A handler for file system events."""

        def __init__(self: "Handler", **kwargs: Any) -> None:
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self: "Handler", event: FileSystemEvent) -> None:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "change": "created",
                    "src_path": event.src_path,
                    "type": event.__class__.__name__,
                    "root_path": root_path,
                },
            )

        def on_deleted(self: "Handler", event: FileSystemEvent) -> None:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "change": "deleted",
                    "src_path": event.src_path,
                    "type": event.__class__.__name__,
                    "root_path": root_path,
                },
            )

        def on_modified(self: "Handler", event: FileSystemEvent) -> None:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "change": "modified",
                    "src_path": event.src_path,
                    "type": event.__class__.__name__,
                    "root_path": root_path,
                },
            )

        def on_moved(self: "Handler", event: FileSystemEvent) -> None:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "change": "moved",
                    "src_path": event.src_path,
                    "type": event.__class__.__name__,
                    "root_path": root_path,
                },
            )

    observer = Observer()
    handler = Handler(ignore_regexes=args.get("ignore_regexes", []))
    observer.schedule(handler, root_path, recursive=args["recursive"])
    observer.start()

    try:
        observer.join()
    finally:
        observer.stop()
        observer.join()


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Watch for changes to a file and put events on the queue."""
    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as task_pool:
        await loop.run_in_executor(task_pool, watch, loop, queue, args)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        def put_nowait(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {"path": "/tmp", "recursive": True}))  # noqa: S108
