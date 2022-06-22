"""
kafka.py

An ansible-events event source plugin for receiving events via a kafka topic.

Arguments:
    host:      The host where the kafka topic is hosted
    port:      The port where the kafka server is listening
    topic:     The kafka topic
    group_id:  A kafka group id



"""


from kafka import KafkaConsumer
import json


def main(queue, args):

    topic = args.get("topic")
    host = args.get("host")
    port = args.get("port")
    group_id = args.get("group_id", None)

    kafka_consumer = KafkaConsumer(
        topic,
        bootstrap_servers="{0}:{1}".format(host, port),
        group_id=group_id,
        enable_auto_commit=False,
        max_poll_records=1,
        auto_offset_reset="earliest",
    )

    for msg in kafka_consumer:
        data = json.loads(msg.value)
        queue.put(data)
        kafka_consumer.commit()
