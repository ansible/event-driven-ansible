"""
file.py

An ansible-rulebook event source plugin for loading facts from YAML files
initially and when the file changes.

Arguments:
    files - a list of YAML files

Example:

    - ansible.eda.file:
      files:
        - fact.yml

"""

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer
import os
import yaml


def send_facts(queue, filename):
    with open(filename) as f:
        data = yaml.safe_load(f.read())
        if data is None:
            return
        if isinstance(data, dict):
            queue.put(data)
        else:
            if not isinstance(data, list):
                raise Exception(
                    f"Unsupported facts type, expects a list of dicts found {type(data)}"
                )
            if not all(True if isinstance(item, dict) else False for item in data):
                raise Exception(
                    f"Unsupported facts type, expects a list of dicts found {data}"
                )
            for item in data:
                queue.put(item)


def main(queue, args):

    files = [os.path.abspath(f) for f in args.get("files", [])]

    if not files:
        return

    for filename in files:
        send_facts(queue, filename)

    class Handler(RegexMatchingEventHandler):
        def __init__(self, **kwargs):
            RegexMatchingEventHandler.__init__(self, **kwargs)

        def on_created(self, event):
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_deleted(self, event):
            pass

        def on_modified(self, event):
            if event.src_path in files:
                send_facts(queue, event.src_path)

        def on_moved(self, event):
            pass

    observer = Observer()
    handler = Handler()

    for filename in files:
        directory = os.path.dirname(filename)
        observer.schedule(handler, directory, recursive=False)

    observer.start()

    try:
        observer.join()
    finally:
        observer.stop()


if __name__ == "__main__":

    class MockQueue:
        def put(self, event):
            print(event)

    main(MockQueue(), {"files": ["facts.yml"]})
