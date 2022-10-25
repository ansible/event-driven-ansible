"""
gcp_pubsub.py

An ansible-events event source module for receiving events from GCP Pub/Sub 

Arguments:
    project_id:      The GCP project name 
    subscription_id: The name of the topic to pull messages from
    max_messages:    The number of messages to retreive
                     Default 3
    retry_deadline:  How long to keep retrying in seconds
                     Default 300

Example:

    - ansible.eda.gpc_pubsub:
        project_id: "{{ project_id }}"
        subscription_id: "{{ subscription_id }}"
        max_messages: "{{ max_messages }}"
        retry_deadline: "{{ retry_deadline }}"

"""

import asyncio
from typing import Any, Dict

from google.api_core import retry
from google.cloud import pubsub_v1

async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    subscriber = pubsub_v1.SubscriberClient()

    subscription_path = subscriber.subscription_path(args.get("project_id"), args.get("subscription_id"))

    with subscriber:
        while True:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": args.get("max_messages", 3)},
                retry=retry.Retry(deadline=args.get("retry_deadline", 300)),
            )

            if len(response.received_messages) == 0:
                continue

            ack_ids = []
            for received_message in response.received_messages:
                data = {"message": received_message.message.data.decode(),
                        "attributes":  dict(received_message.message.attributes)}

                await queue.put(data)

                ack_ids.append(received_message.ack_id)

            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )

            await asyncio.sleep(1)

if __name__ == "__main__":
    class MockQueue:
        @staticmethod
        async def put(self, event):
            print(event)

    asyncio.run(main(MockQueue(), {"project_id": "lab", "subscription_id": "eda",
                                   "max_messages": 3, "retry_deadline": 300}))

