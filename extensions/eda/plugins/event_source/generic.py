"""A generic source plugin that allows you to insert custom data.

The event data to insert into the queue is specified in the required
parameter payload and is an array of events.

Optional Parameters:
payload_file A yaml with an array of events can be used instead of payload
randomize    True|False Randomize the events in the payload, default False
display      True|False Display the event data in stdout, default False
timestamp    True|False Add an event timestamp, default False
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
loop_count int     Number of times the set of events in the payload
                   should be repeated. Default 0
repeat_count int   Number of times each individual event in the payload
                   should be repeated. Default 1
blob_size int      An arbitrary blob of blob_size bytes to be inserted
                   into every event payload. Default is 0 don't create
                   a blob
final_payload dict After all the events have been sent we send the optional
                   final payload which can be used to trigger a shutdown of
                   the rulebook, especially when we are using rulebooks to
                   forward messages to other running rulebooks.


"""

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

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Args:
    """Class to store all the passed in args."""

    payload: Any
    final_payload: Any = None
    display: bool = False
    create_index: str = ""
    payload_file: str = ""


@dataclass
class ControlArgs:
    """Class to store the control of payload."""

    randomize: bool = False
    time_format: str = "local"
    blob_size: int = 0
    loop_count: int = 1
    repeat_count: int = 1
    timestamp: bool = False


@dataclass
class DelayArgs:
    """Class to store the delays when inserting events."""

    startup_delay: float = 0
    event_delay: float = 0
    repeat_delay: float = 0
    shutdown_after: float = 0
    loop_delay: float = 0


class Generic:
    """Generic source plugin to generate different events."""

    def __init__(
        self: Generic, queue: asyncio.Queue[Any], args: dict[str, Any]
    ) -> None:
        """Insert event data into the queue."""
        self.queue = queue
        field_names = [f.name for f in fields(Args)]

        if "payload_file" in args:
            args["payload"] = ""

        self.my_args = Args(**{k: v for k, v in args.items() if k in field_names})
        field_names = [f.name for f in fields(ControlArgs)]
        self.control_args = ControlArgs(
            **{k: v for k, v in args.items() if k in field_names},
        )
        field_names = [f.name for f in fields(DelayArgs)]
        self.delay_args = DelayArgs(
            **{k: v for k, v in args.items() if k in field_names},
        )
        self.blob = (
            "x" * self.control_args.blob_size
            if self.control_args.blob_size > 0
            else None
        )

    async def __call__(self: Generic) -> None:
        """Run the generic source plugin."""
        if self.control_args.timestamp and self.control_args.time_format not in [
            "local",
            "iso8601",
            "epoch",
        ]:
            msg = "time_format must be one of local, iso8601, epoch"
            raise ValueError(msg)

        await self._load_payload_from_file()

        if not isinstance(self.my_args.payload, list):
            self.my_args.payload = [self.my_args.payload]

        iteration = 0
        index = 0

        await asyncio.sleep(self.delay_args.startup_delay)

        while iteration != self.control_args.loop_count:
            if self.delay_args.loop_delay > 0 and iteration > 0:
                await asyncio.sleep(self.delay_args.loop_delay)
            if self.control_args.randomize:
                random.shuffle(self.my_args.payload)
            for event in self.my_args.payload:
                if not event:
                    continue
                for _ignore in range(self.control_args.repeat_count):
                    await self._post_event(event, index)
                    index += 1
                    await asyncio.sleep(self.delay_args.repeat_delay)

                await asyncio.sleep(self.delay_args.event_delay)
            iteration += 1

        if isinstance(self.my_args.final_payload, dict):
            await self._post_event(self.my_args.final_payload, index)

        await asyncio.sleep(self.delay_args.shutdown_after)

    async def _post_event(self: Generic, event: dict[str, Any], index: int) -> None:
        data = self._create_data(index)

        data.update(event)
        if self.my_args.display:
            print(data)  # noqa: T201
        await self.queue.put(data)

    async def _load_payload_from_file(self: Generic) -> None:
        if not self.my_args.payload_file:
            return
        path = Path(self.my_args.payload_file)
        if not path.is_file():
            msg = f"File {self.my_args.payload_file} not found"
            raise ValueError(msg)
        with path.open(mode="r", encoding="utf-8") as file:
            try:
                self.my_args.payload = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                msg = f"File {self.my_args.payload_file} parsing error {exc}"
                raise ValueError(msg) from exc

    def _create_data(
        self: Generic,
        index: int,
    ) -> dict[str, Any]:
        data: dict[str, str | int] = {}
        if self.my_args.create_index:
            data[self.my_args.create_index] = index
        if self.blob:
            data["blob"] = self.blob
        if self.control_args.timestamp:
            if self.control_args.time_format == "local":
                data["timestamp"] = str(datetime.now())  # noqa: DTZ005
            elif self.control_args.time_format == "epoch":
                data["timestamp"] = int(time.time())
            elif self.control_args.time_format == "iso8601":
                data["timestamp"] = datetime.now(tz=None).isoformat()  # noqa: DTZ005
        return data


async def main(  # pylint: disable=R0914
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Call the Generic Source Plugin."""
    await Generic(queue, args)()


if __name__ == "__main__":

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: MockQueue, event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {
                "randomize": True,
                "startup_delay": 1,
                "create_index": "my_index",
                "loop_count": 2,
                "repeat_count": 2,
                "repeat_delay": 1,
                "event_delay": 2,
                "loop_delay": 3,
                "shutdown_after": 11,
                "timestamp": True,
                "display": True,
                "payload": [{"i": 1}, {"f": 3.14159}, {"b": False}],
            },
        ),
    )
