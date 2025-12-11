"""Event source plugin for receiving events from AWS CloudTrail.

This module provides an event source plugin for getting events from AWS CloudTrail
using the aiobotocore library. It supports all authentication methods provided by boto.
"""

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from aiobotocore.session import get_session
from botocore.client import BaseClient

if TYPE_CHECKING:
    from collections.abc import Awaitable

DOCUMENTATION = r"""
---
short_description: Receive events from an AWS CloudTrail
description:
  - An ansible-rulebook event source module for getting events from an AWS CloudTrail.
  - >
    This supports all the authentication methods supported by boto library:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
options:
  access_key:
    description:
      - Optional AWS access key ID.
    type: str
  secret_key:
    description:
      - Optional AWS secret access key.
    type: str
  session_token:
    description:
      - Optional STS session token for use with temporary credentials.
    type: str
  endpoint_url:
    description:
      - Optional URL to connect to instead of the default AWS endpoints.
    type: str
  region:
    description:
      - Optional AWS region to use.
    type: str
  delay_seconds:
    description:
      - The number of seconds to wait between polling.
    type: int
    default: 10
  lookup_attributes:
    description:
      - The optional list of lookup attributes.
      - A lookup attribute is a dictionary containing an AttributeKey (string),
        which specifies the attribute used to filter returned events, and an
        AttributeValue (string), which defines the value for the specified AttributeKey.
    type: list
    elements: str
  event_category:
    description:
      - The optional event category to return. (e.g. 'insight')
    type: str
"""

EXAMPLES = r"""
- ansible.eda.aws_cloudtrail:
    region: us-east-1
    lookup_attributes:
      - AttributeKey: 'EventSource'
        AttributeValue: 'ec2.amazonaws.com'
      - AttributeKey: 'ReadOnly'
        AttributeValue: 'true'
    event_category: management
"""


def _cloudtrail_event_to_dict(event: dict[str, Any]) -> dict[str, Any]:
    """Convert CloudTrail event to dictionary format.

    :param event: The CloudTrail event to convert
    :type event: dict[str, Any]
    :returns: Converted event dictionary with parsed CloudTrailEvent
    :rtype: dict[str, Any]
    """
    event["EventTime"] = event["EventTime"].isoformat()
    event["CloudTrailEvent"] = json.loads(event["CloudTrailEvent"])
    return event


def _get_events(
    events: list[dict[str, Any]],
    last_event_ids: list[str],
) -> tuple[list[dict[str, Any]], Any, list[str]]:
    """Filter and process CloudTrail events.

    :param events: List of CloudTrail events to process
    :type events: list[dict[str, Any]]
    :param last_event_ids: List of event IDs from previous iteration
    :type last_event_ids: list[str]
    :returns: Tuple of (filtered events, latest event time, latest event IDs)
    :rtype: tuple[list[dict[str, Any]], Any, list[str]]
    """
    event_time = None
    event_ids = []
    result = []
    for event in events:
        # skip last event
        if last_event_ids and event["EventId"] in last_event_ids:
            continue
        if event_time is None or event_time < event["EventTime"]:
            event_time = event["EventTime"]
            event_ids = [event["EventId"]]
        elif event_time == event["EventTime"]:
            event_ids.append(event["EventId"])
        result.append(event)
    return result, event_time, event_ids


async def _get_cloudtrail_events(
    client: BaseClient,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Get CloudTrail events using paginator.

    :param client: The boto client for CloudTrail
    :type client: BaseClient
    :param params: Parameters for the lookup_events API call
    :type params: dict[str, Any]
    :returns: List of CloudTrail events
    :rtype: list[dict[str, Any]]
    """
    paginator = client.get_paginator("lookup_events")
    results: dict[str, Any] = await cast(
        "Awaitable[dict[str, Any]]",
        paginator.paginate(**params).build_full_result(),
    )
    events = results.get("Events", [])
    # type guards:
    if not isinstance(events, list):
        err_msg = "Events is not a list"
        raise TypeError(err_msg)
    for event in events:
        if not isinstance(event, dict):
            err_msg = "Event is not a dictionary"
            raise TypeError(err_msg)
    return events


ARGS_MAPPING = {
    "lookup_attributes": "LookupAttributes",
    "event_category": "EventCategory",
}


async def main(queue: asyncio.Queue[Any], args: dict[str, Any]) -> None:
    """Receive events via AWS CloudTrail.

    Main entry point for the AWS CloudTrail event source plugin. Continuously polls
    CloudTrail for new events and puts them into the queue.

    :param queue: The asyncio queue to put events into
    :type queue: asyncio.Queue[Any]
    :param args: Configuration arguments for the event source
    :type args: dict[str, Any]
    :returns: None
    :rtype: None
    """
    delay = int(args.get("delay_seconds", 10))

    session = get_session()
    params = {}
    for key, value in ARGS_MAPPING.items():
        if args.get(key) is not None:
            params[value] = args.get(key)

    params["StartTime"] = datetime.utcnow()  # noqa: DTZ003

    async with session.create_client("cloudtrail", **connection_args(args)) as client:
        event_time = None
        event_ids: list[str] = []
        while True:
            if event_time is not None:
                params["StartTime"] = event_time
            events = await _get_cloudtrail_events(client, params)

            events, c_event_time, c_event_ids = _get_events(events, event_ids)
            for event in events:
                await queue.put(_cloudtrail_event_to_dict(event))

            event_ids = c_event_ids or event_ids
            event_time = c_event_time or event_time

            await asyncio.sleep(delay)


def connection_args(args: dict[str, Any]) -> dict[str, Any]:
    """Provide connection arguments to AWS CloudTrail.

    :param args: Configuration arguments containing AWS credentials
    :type args: dict[str, Any]
    :returns: Dictionary of connection arguments for boto client
    :rtype: dict[str, Any]
    """
    selected_args = {}

    # Best Practice: get credentials from ~/.aws/credentials or the environment
    # However the following method are still possible
    if "access_key" in args:
        selected_args["aws_access_key_id"] = args["access_key"]
    if "secret_key" in args:
        selected_args["aws_secret_access_key"] = args["secret_key"]
    if "session_token" in args:
        selected_args["aws_session_token"] = args["session_token"]

    if "endpoint_url" in args:
        selected_args["endpoint_url"] = args["endpoint_url"]
    if "region" in args:
        selected_args["region_name"] = args["region"]
    return selected_args


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(main(MockQueue(), {}))
