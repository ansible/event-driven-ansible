"""
file_watch.py

An ansible-rulebook event source plugin for watching file system changes.

Arguments:
    path: The directory to watch for changes.
    ignore_regexes: A list of regular expressions to ignore changes
    recursive: Recursively watch the path if true

Example:

    - name: file_watch
      file_watch:
        path: "{{src_path}}"
        recursive: true
        ignore_regexes: ['.*\\.pytest.*', '.*__pycache__.*', '.*/.git.*']
"""

import asyncio
import concurrent.futures

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


def watch(loop, queue, args):

    root_path = args["path"]

    class Handler(RegexMatchingEventHandler):
        def __init__(self, **kwargs):
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self, event):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                dict(
                    change="created",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                ),
            )

        def on_deleted(self, event):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                dict(
                    change="deleted",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                ),
            )

        def on_modified(self, event):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                dict(
                    change="modified",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                ),
            )

        def on_moved(self, event):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                dict(
                    change="moved",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                ),
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


async def main(queue, args):
    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as task_pool:
        await loop.run_in_executor(task_pool, watch, loop, queue, args)


if __name__ == "__main__":

    class MockQueue:
        def put_nowait(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"path": "/tmp", "recursive": True}))
