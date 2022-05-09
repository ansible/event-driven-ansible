
"""

url_check.py

An ansible-events event source plugin that polls a set of URLs and sends
events with their status.

Arguments:

    urls - a list of urls to poll
    delay - the number of seconds to wait between polling

Example:

    - name: check web server
      benthomasson.eda.url_check:
        urls:
          - http://44.201.5.56:8000/docs
        delay: 10
"""

import requests
import time
from requests.exceptions import ConnectionError


def main(queue, args):

    urls = args.get('urls', [])
    delay = args.get('delay', 1)

    if not urls:
        return

    while True:

        for url in urls:
            try:
                response = requests.get(url)
                queue.put(dict(url_check=dict(url=url,
                                              status='up' if response.status_code == 200 else 'down',
                                              status_code=response.status_code)))

            except ConnectionError:
                queue.put(dict(url_check=dict(url=url,
                                              status='down',
                                              status_code=None)))
        time.sleep(delay)




if __name__ == "__main__":
    class MockQueue:
        def put(self, event):
            print(event)

    main(MockQueue(), {'urls': ['http://redhat.com']})


