#!/usr/bin/env python3
"""
template.py

An ansible-rulebook event emitter plugin template.

Examples:
  sources:
    - template:

"""
import asyncio
from typing import Any, Dict


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    # The main entrypoint for the emitter plugin.
    # This function is called by the rulebook engine.
    # The queue is used to send messages from the rulebook engine to the plugin.
    # The args dictionary contains the arguments passed to the plugin in the rulebook.
    delay = args.get("delay", 0)

    while True:
        # Get a message from the queue.
        # This is a blocking call, so the plugin will wait here until a message is available.
        message = await queue.get()
        # Do something with the message.
        # This is where you would send the message to a remote service.
        # If the message is None, then the rulebook engine is shutting down.
        if message is None:
            break
        # Here we just print the message as an example.
        print(message)


if __name__ == "__main__":
    # Test your plugin locally by running this file directly.

    # We use the MockQueue class to simulate the queue for testing.
    # In production, the queue will be provided by the rulebook engine.
    class MockQueue:
        count = 10
        async def get(self):
            self.count -= 1
            if self.count == 0:
                return None
            else:
                return {'message': 'hello world'}

    mock_arguments = dict()
    asyncio.run(main(MockQueue(), mock_arguments))

