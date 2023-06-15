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

import os

import yaml
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


def send_facts(queue, filename):
    with open(filename) as f:
        data = yaml.safe_load(f.read())
        if data is None:
            return
        if isinstance(data, dict):
            queue.put(data)
        else:
            if not isinstance(data, list):
                msg = f"Unsupported facts type, expects a list of dicts found {type(data)}"
                raise Exception(
                    msg,
                )
            if not all(bool(isinstance(item, dict)) for item in data):
                msg = f"Unsupported facts type, expects a list of dicts found {data}"
                raise Exception(
                    msg,
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
        def __init__(self, **kwargs) -> None:
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
