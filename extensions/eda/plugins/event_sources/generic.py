#  Copyright 2022 Red Hat, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import asyncio
import random
import time
from datetime import datetime
from typing import Any, Dict

""" A generic source plugin that allows you to insert custom data

    The event data to insert into the queue is specified in the required
    parameter payload and is an array of events.

    Optional Parameters:
    randomize    True|False Randomize the events in the payload, default False
    display      True|False Display the event data in stdout, default False
    add_timestamp True|False Add an event timestamp, default False
    time_format   local|iso8601|epoch  The time format of event timestamp,
                  default local
    create_index str   The index to create for each event starts at 0
    startup_delay float  Number of seconds to wait before injecting events
                       into the queue. Default 0
    event_delay float    Number of seconds to wait before injecting the next
                       event from the payload. Default 0
    repeat_delay float   Number of seconds to wait before injecting a repeated
                       event from the payload. Default 0
    loop_delay float     Number of seconds to wait before inserting the
                       next set of events. Default 0
    shutdown_after float Number of seconds to wait before shutting down the
                       plugin. Default 0
    loop_count int     Number of times the set of events in the playload
                       should be repeated. Default 0
    repeat_count int   Number of times each individual event in the playload
                       should be repeated. Default 1

"""


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    payload = args.get("payload")
    randomize = args.get("randomize", False)
    display = args.get("display", False)
    add_timestamp = args.get("timestamp", False)
    time_format = args.get("time_format", "local")
    create_index = args.get("create_index", "")

    startup_delay = float(args.get("startup_delay", 0))
    event_delay = float(args.get("event_delay", 0))
    repeat_delay = float(args.get("repeat_delay", 0))
    loop_delay = float(args.get("loop_delay", 0))
    shutdown_after = float(args.get("shutdown_after", 0))

    loop_count = int(args.get("loop_count", 1))  # -1 infinite
    repeat_count = int(args.get("repeat_count", 1))
    if time_format not in ["local", "iso8601", "epoch"]:
        raise ValueError("time_format must be one of local, iso8601, epoch")

    if not isinstance(payload, list):
        payload = [payload]

    iteration = 0
    index = 0

    await asyncio.sleep(startup_delay)

    while iteration != loop_count:
        if loop_delay > 0 and iteration > 0:
            await asyncio.sleep(loop_delay)
        if randomize:
            random.shuffle(payload)
        for event in payload:
            if not event:
                continue
            for _ in range(repeat_count):
                data = {}
                if create_index:
                    data[create_index] = index
                if add_timestamp:
                    if time_format == "local":
                        data["timestamp"] = str(datetime.now())
                    elif time_format == "epoch":
                        data["timestamp"] = int(time.time())
                    elif time_format == "iso8601":
                        data["timestamp"] = datetime.now().isoformat()

                index += 1
                data.update(event)
                if display:
                    print(data)
                await queue.put(data)
                await asyncio.sleep(repeat_delay)

            await asyncio.sleep(event_delay)
        iteration += 1
    await asyncio.sleep(shutdown_after)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(event)

    asyncio.run(
        main(
            MockQueue(),
            dict(
                randomize=True,
                startup_delay=1,
                create_index="my_index",
                loop_count=2,
                repeat_count=2,
                repeat_delay=1,
                event_delay=2,
                loop_delay=3,
                shutdown_after=11,
                timestamp=True,
                display=True,
                payload=[dict(i=1), dict(f=3.14159), dict(b=False)],
            ),
        )
    )
