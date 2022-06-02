"""
range.py

An ansible-events event source plugin for generating events with an increasing index i.

Arguments:
    limit: The upper limit of the range of the index.

Example:

    - benthomasson.eda.range:
        limit: 5

"""

import time


def main(queue, args):

    delay = args.get("delay", 0)

    for i in range(int(args["limit"])):
        queue.put(dict(i=i))
        if delay:
            time.sleep(delay)


if __name__ == "__main__":

    class MockQueue:
        def put(self, event):
            print(event)

    main(MockQueue(), dict(limit=5, delay=1))
