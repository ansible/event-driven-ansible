"""
watchdog.py

An ansible-rulebook event source plugin for watching file system changes.

Arguments:
    path: The directory to watch for changes.
    ignore_regexes: A list of regular expressions to ignore changes
    recursive: Recursively watch the path if true

Example:

    - ansible.eda.watchdog:
        path: "{{src_path}}"
        recursive: true
        ignore_regexes: ['.*.pytest.*', '.*__pycache__.*', '.*/.git.*']
"""

import os

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


def main(queue, args):

    root_path = os.path.abspath(args["path"])

    class Handler(RegexMatchingEventHandler):
        def __init__(self, **kwargs):
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self, event):
            queue.put(
                dict(
                    change="created",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                )
            )

        def on_deleted(self, event):
            queue.put(
                dict(
                    change="deleted",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                )
            )

        def on_modified(self, event):
            queue.put(
                dict(
                    change="modified",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                )
            )

        def on_moved(self, event):
            queue.put(
                dict(
                    change="moved",
                    src_path=event.src_path,
                    type=event.__class__.__name__,
                    root_path=root_path,
                )
            )

    observer = Observer()
    handler = Handler(ignore_regexes=args.get("ignore_regexes"))
    observer.schedule(handler, root_path, recursive=args["recursive"])
    observer.start()

    try:
        observer.join()
    finally:
        observer.stop()
        observer.join()
