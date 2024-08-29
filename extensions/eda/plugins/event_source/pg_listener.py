"""pg_listener.py.

An ansible-rulebook event source plugin for reading events from
pg_pub_sub

Arguments:
---------
    dsn: The connection string/dsn for Postgres
    channels: The list of channels to listen

Example:
-------
    - ansible.eda.pg_listener:
        dsn: "host=localhost port=5432 dbname=mydb"
        channels:
          - my_events
          - my_alerts

Chunking:
---------
   This is just informational a user doesn't have to do anything
   special to enable chunking. The sender which is the pg_notify
   action from ansible rulebook will decide if chunking needs to
   happen based on the size of the payload.
   If the messages are over 7KB the sender will chunk the messages
   into separate payloads with each payload having having the following
   keys
   * _message_chunked_uuid   The unique message uuid
   * _message_chunk_count    The number of chunks for the message
   * _message_chunk_sequence The sequence of the current chunk
   * _chunk                  The actual chunk
   * _message_length         The total length of the message
   * _message_xx_hash        A hash for the entire message

   The pg_listener source will assemble the chunks and once all the
   chunks have been received it will deliver the entire payload to the
   rulebook engine. Before the payload is delivered we validated that the entire
   message has been received by validate its computed hash.

"""

import asyncio
import json
import logging
from typing import Any

import xxhash
from psycopg import AsyncConnection, OperationalError

LOGGER = logging.getLogger(__name__)

MESSAGE_CHUNKED_UUID = "_message_chunked_uuid"
MESSAGE_CHUNK_COUNT = "_message_chunk_count"
MESSAGE_CHUNK_SEQUENCE = "_message_chunk_sequence"
MESSAGE_CHUNK = "_chunk"
MESSAGE_LENGTH = "_message_length"
MESSAGE_XX_HASH = "_message_xx_hash"
REQUIRED_KEYS = ("dsn", "channels")

REQUIRED_CHUNK_KEYS = (
    MESSAGE_CHUNK_COUNT,
    MESSAGE_CHUNK_SEQUENCE,
    MESSAGE_CHUNK,
    MESSAGE_LENGTH,
    MESSAGE_XX_HASH,
)


class MissingRequiredArgumentError(Exception):
    """Exception class for missing arguments."""

    def __init__(self: "MissingRequiredArgumentError", key: str) -> None:
        """Class constructor with the missing key."""
        super().__init__(f"PG Listener {key} is a required argument")


class MissingChunkKeyError(Exception):
    """Exception class for missing chunking keys."""

    def __init__(self: "MissingChunkKeyError", key: str) -> None:
        """Class constructor with the missing key."""
        super().__init__(f"Chunked payload is missing required {key}")


def _validate_chunked_payload(payload: dict[str, Any]) -> None:
    for key in REQUIRED_CHUNK_KEYS:
        if key not in payload:
            raise MissingChunkKeyError(key)


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Listen for events from a channel."""
    for key in REQUIRED_KEYS:
        if key not in args:
            raise MissingRequiredArgumentError(key)

    try:
        async with await AsyncConnection.connect(
            conninfo=args["dsn"],
            autocommit=True,
        ) as conn:
            chunked_cache: dict[str, Any] = {}
            cursor = conn.cursor()
            for channel in args["channels"]:
                await cursor.execute(f"LISTEN {channel};")
                LOGGER.debug("Waiting for notifications on channel %s", channel)
            async for event in conn.notifies():
                data = json.loads(event.payload)
                if MESSAGE_CHUNKED_UUID in data:
                    _validate_chunked_payload(data)
                    await _handle_chunked_message(data, chunked_cache, queue)
                else:
                    await queue.put(data)
    except json.decoder.JSONDecodeError:
        LOGGER.exception("Error decoding data")
        raise
    except OperationalError:
        LOGGER.exception("PG Listen operational error")
        raise


async def _handle_chunked_message(
    data: dict[str, Any],
    chunked_cache: dict[str, Any],
    queue: asyncio.Queue[Any],
) -> None:
    message_uuid = data[MESSAGE_CHUNKED_UUID]
    number_of_chunks = data[MESSAGE_CHUNK_COUNT]
    message_length = data[MESSAGE_LENGTH]
    LOGGER.debug(
        "Received chunked message %s total chunks %d message length %d",
        message_uuid,
        number_of_chunks,
        message_length,
    )
    if message_uuid in chunked_cache:
        chunked_cache[message_uuid].append(data)
    else:
        chunked_cache[message_uuid] = [data]
    if (
        len(chunked_cache[message_uuid])
        == chunked_cache[message_uuid][0][MESSAGE_CHUNK_COUNT]
    ):
        LOGGER.debug(
            "Received all chunks for message %s",
            message_uuid,
        )
        all_data = ""
        for chunk in chunked_cache[message_uuid]:
            all_data += chunk[MESSAGE_CHUNK]
        chunks = chunked_cache.pop(message_uuid)
        xx_hash = xxhash.xxh32(all_data.encode("utf-8")).hexdigest()
        LOGGER.debug("Computed XX Hash is %s", xx_hash)
        LOGGER.debug(
            "XX Hash expected %s",
            chunks[0][MESSAGE_XX_HASH],
        )
        if xx_hash == chunks[0][MESSAGE_XX_HASH]:
            data = json.loads(all_data)
            await queue.put(data)
        else:
            LOGGER.error("XX Hash of chunked payload doesn't match")
    else:
        LOGGER.debug(
            "Received %d chunks for message %s",
            len(chunked_cache[message_uuid]),
            message_uuid,
        )


if __name__ == "__main__":
    # MockQueue if running directly

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {
                "dsn": "host=localhost port=5432 dbname=eda "
                "user=postgres password=secret",
                "channels": ["my_channel"],
            },
        ),
    )
