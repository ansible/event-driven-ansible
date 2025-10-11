import asyncio
import json
import logging
import os
import sys
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

try:
    from .oauth_tokens import create_oauth_provider
except ImportError:
    # Since ansible-rulebook launches the source plugin via
    # run_py.run_path it doesn't set the python path and the
    # import fails, hence this workaround.
    module_directory = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(module_directory)
    from oauth_tokens import create_oauth_provider  # type: ignore

DEFAULT_SASL_MECHANISM = "PLAIN"
DEFAULT_OFFSET = "latest"
DEFAULT_VERIFY_MODE = "CERT_REQUIRED"
VERIFY_MODES = {
    "CERT_NONE": CERT_NONE,
    "CERT_OPTIONAL": CERT_OPTIONAL,
    "CERT_REQUIRED": CERT_REQUIRED,
}

SUPPORTED_SASL_MECHANISMS = [
    "PLAIN",
    "SCRAM-SHA-256",
    "SCRAM-SHA-512",
    "GSSAPI",
    "OAUTHBEARER",
]
USER_PASSWORD_MECHANISMS = ["SCRAM-SHA-256", "SCRAM-SHA-512"]
PLAIN_CREDENTIAL_KEYS = ["sasl_plain_username", "sasl_plain_password"]

DOCUMENTATION = r"""
---
short_description: Receive events via a kafka topic.
description:
  - An ansible-rulebook event source plugin for receiving events via a kafka topic.
options:
  host:
    description:
      - The host where the kafka topic is hosted.
    type: str
    required: true
  port:
    description:
      - The port where the kafka server is listening.
    type: str
    required: true
  cafile:
    description:
      - The optional certificate authority file path containing certificates
        used to sign kafka broker certificates
    type: str
  certfile:
    description:
      - The optional client certificate file path containing the client
        certificate, as well as CA certificates needed to establish
        the certificates authenticity.
    type: str
  keyfile:
    description:
      - The optional client key file path containing the client private key.
    type: str
  password:
    description:
      - The optional password to be used when loading the certificate chain.
    type: str
  check_hostname:
    description:
      - Enable SSL hostname verification.
    type: bool
    default: true
  verify_mode:
    description:
      - Whether to try to verify other peers' certificates and how to
        behave if verification fails.
    type: str
    default: "CERT_REQUIRED"
    choices: ["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"]
  encoding:
    description:
      - Message encoding scheme.
    type: str
    default: "utf-8"
  topic:
    description:
      - The kafka topic. topic, topics, and topic_pattern are mutually exclusive.
    type: str
  topics:
    description:
      - The kafka topics. topic, topics, and topic_pattern are mutually exclusive.
    type: list
    elements: str
  topic_pattern:
    description:
      - The kafka topic pattern. It must be a valid regex. topic, topics, and topic_pattern are mutually exclusive.
        [AIOKafkaConsumer](https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.AIOKafkaConsumer) performs
        periodic metadata refreshes in the background and will notice when new partitions are added to one of the
        subscribed topics or when a new topic matching a subscribed regex is created. See metadata_max_age_ms for
        more details on how to configure the metadata refresh.
    type: str
  metadata_max_age_ms:
    description:
      - The period of time in milliseconds for forcing a refresh of metadata.
        It configures how soon a topic or partition change is detected. Default to 5 minutes.
    type: int
    default: 300000 # 5 minutes
  group_id:
    description:
      - A kafka group id.
    type: str
    default: null
  offset:
    description:
      - Where to automatically reset the offset.
    type: str
    default: "latest"
    choices: ["latest", "earliest"]
  security_protocol:
    description:
      - Protocol used to communicate with brokers.
    type: str
    default: "PLAINTEXT"
    choices: ["PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"]
  sasl_mechanism:
    description:
      - Authentication mechanism when security_protocol is configured.
    type: str
    default: "PLAIN"
    choices: ["PLAIN", "GSSAPI", "SCRAM-SHA-256", "SCRAM-SHA-512", "OAUTHBEARER"]
  sasl_plain_username:
    description:
      - Username for SASL PLAIN authentication.
    type: str
  sasl_plain_password:
    description:
      - Password for SASL PLAIN authentication.
    type: str
  sasl_kerberos_service_name:
    description:
      - The service name, default is kafka
    type: str
  sasl_kerberos_domain_name:
    description:
      - The kerberos REALM
    type: str
  sasl_oauth_token_endpoint:
    description:
      - The URL to get the OAuth2 token from your Authorization Server
    type: str
  sasl_oauth_client_id:
    description:
      - The id used when fetching the token from Authorization Server
    type: str
  sasl_oauth_client_secret:
    description:
      - The secret used when fetching the token from Authorization Server.
        This is not needed if you are using private_key_jwt
    type: str
  sasl_oauth_private_keyfile:
    description:
      - When using the private_key_jwt this specifies the private key file
        This is not needed if you are using regular oauth flow
    type: str
  sasl_oauth_public_keyfile:
    description:
      - When using the private_key_jwt this specifies the public key file
        This is not needed if you are using regular oauth flow
        Some of the Authorization Servers require that the public key
        signature be sent instead of the key id
        If a public key file is specified the JWT Header will have the
        x5t X.509 Certificate SHA-1 Thumb print
        x5t#S256 X.509 Certificate SHA-256 Thumb print
        If this field is missing we wont set these in the JWT Header
    type: str
  sasl_oauth_issuer:
    description:
      - When using the private_key_jwt this specifies the issuer (iss)
        that will be set in the JWT header, by default this value
        is set to be the same as sasl_oauth_client_id
    type: str
    default: the same value as sasl_oauth_client_id
  sasl_oauth_subject:
    description:
      - When using the private_key_jwt this specifies the issuer (sub)
        that will be set in the JWT header, by default this value
        is set to be the same as sasl_oauth_client_id
    type: str
    default: the same value as sasl_oauth_client_id
  sasl_oauth_audience:
    description:
      - When using the private_key_jwt this specifies the audience (aud)
        that will be set in the JWT header, by default this value
        is set to be the same as sasl_oauth_token_endpoint
    type: str
    default: the same value as sasl_oauth_token_endpoint
  sasl_oauth_token_duration:
    description:
      - The life span of the token specified in minutes
        The default is 30 minutes
    type: int
    default: 30
  sasl_oauth_algorithm:
    description:
      - When using the private_key_jwt the algorithm to use in jwt
        that will be set in the JWT header, by default this value
        is set to be RS256
    type: str
    default: "RS256"
  sasl_oauth_method:
    description:
      - When fetching a token from a Auth Server you can choose from
        client_secret_basic, client_secret_post
        client_secret_jwt, private_key_jwt
    type: str
    default: "client_secret_basic"
  sasl_oauth_scope:
    description:
      - The optional scope when using OAUTHBEARER
    type: str
"""

EXAMPLES = r"""
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    check_hostname: true
    verify_mode: "CERT_OPTIONAL"
    encoding: "utf-8"
    topics:
      - "demo"
      - "demo2"
    group_id: "test"
    offset: "earliest"
    security_protocol: "SASL_PLAINTEXT"
    sasl_mechanism: "GSSAPI"
    sasl_plain_username: "admin"
    sasl_plain_password: "test"
"""


def _validate_args(args: dict[str, Any]) -> None:

    sasl_mechanism = args.get("sasl_mechanism", DEFAULT_SASL_MECHANISM)
    verify_mode = args.get("verify_mode", DEFAULT_VERIFY_MODE)
    offset = args.get("offset", DEFAULT_OFFSET)

    if sasl_mechanism not in SUPPORTED_SASL_MECHANISMS:
        msg = (
            f"SASL Mechanism {sasl_mechanism} is not supported: "
            f"valid mechanisms are {SUPPORTED_SASL_MECHANISMS}"
        )
        raise ValueError(msg)

    if sasl_mechanism in USER_PASSWORD_MECHANISMS:
        for key in PLAIN_CREDENTIAL_KEYS:
            if key not in args:
                msg = (
                    f"For sasl_mechanism {sasl_mechanism}, {key} is missing."
                    "Please specify all of the following arguments: "
                    f"{','.join(PLAIN_CREDENTIAL_KEYS)}"
                )
                raise ValueError(msg)

    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    if verify_mode not in VERIFY_MODES:
        msg = f"Invalid verify_mode option: {verify_mode}"
        raise ValueError(msg)


async def main(  # pylint: disable=R0914
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
    logger = logging.getLogger()

    topic = args.get("topic")
    topics = args.get("topics")
    topic_pattern = args.get("topic_pattern")

    num_topics = sum(1 for tp in (topic, topics, topic_pattern) if tp is not None)
    if num_topics != 1:
        msg = "Exactly one of topic, topics, or topic_pattern must be provided."
        raise ValueError(msg)

    if topic:
        topics = [topic]

    host = args.get("host")
    port = args.get("port")
    cafile = args.get("cafile")
    certfile = args.get("certfile")
    keyfile = args.get("keyfile")
    password = args.get("password")
    check_hostname = args.get("check_hostname", True)
    verify_mode = args.get("verify_mode", DEFAULT_VERIFY_MODE)
    group_id = args.get("group_id")
    offset = args.get("offset", DEFAULT_OFFSET)
    encoding = args.get("encoding", "utf-8")
    security_protocol = args.get("security_protocol", "PLAINTEXT")
    sasl_mechanism = args.get("sasl_mechanism", DEFAULT_SASL_MECHANISM)
    sasl_oauth_token_provider = None

    _validate_args(args)

    if sasl_mechanism == "OAUTHBEARER":

        sasl_oauth_token_provider = create_oauth_provider(args)

    ssl_context = None
    verify_mode = VERIFY_MODES[verify_mode]
    if cafile or security_protocol.endswith("SSL"):
        security_protocol = security_protocol.replace("PLAINTEXT", "SSL")
        ssl_context = create_ssl_context(
            cafile=cafile,
            certfile=certfile,
            keyfile=keyfile,
            password=password,
        )
        ssl_context.check_hostname = check_hostname
        ssl_context.verify_mode = verify_mode

    kafka_consumer = AIOKafkaConsumer(
        bootstrap_servers=f"{host}:{port}",
        group_id=group_id,
        enable_auto_commit=True,
        max_poll_records=1,
        auto_offset_reset=offset,
        security_protocol=security_protocol,
        ssl_context=ssl_context,
        sasl_mechanism=args.get("sasl_mechanism", DEFAULT_SASL_MECHANISM),
        sasl_plain_username=args.get("sasl_plain_username"),
        sasl_plain_password=args.get("sasl_plain_password"),
        sasl_kerberos_service_name=args.get("sasl_kerberos_service_name"),
        sasl_kerberos_domain_name=args.get("sasl_kerberos_domain_name"),
        metadata_max_age_ms=int(args.get("metadata_max_age_ms", 300000)),
        sasl_oauth_token_provider=sasl_oauth_token_provider,
    )

    kafka_consumer.subscribe(topics=topics, pattern=topic_pattern)

    await kafka_consumer.start()

    try:
        await receive_msg(queue, kafka_consumer, encoding)
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()


async def receive_msg(
    queue: asyncio.Queue[Any],
    kafka_consumer: AIOKafkaConsumer,
    encoding: str,
) -> None:
    """Receive messages from the Kafka topic and put them into the queue."""
    logger = logging.getLogger()

    async for msg in kafka_consumer:
        event: dict[str, Any] = {}

        # Process headers
        try:
            headers: dict[str, str] = {
                header[0]: header[1].decode(encoding) for header in msg.headers
            }
            event["meta"] = {}
            event["meta"]["headers"] = headers
        except UnicodeError:
            logger.exception("Unicode error while decoding headers")

        # Process message body
        try:
            value = msg.value.decode(encoding)
            data = json.loads(value)
        except json.decoder.JSONDecodeError:
            logger.info("JSON decode error, storing raw value")
            data = value
        except UnicodeError:
            logger.exception("Unicode error while decoding message body")
            data = None

        # Add data to the event and put it into the queue
        if data:
            event["body"] = data
            await queue.put(event)

        await asyncio.sleep(0)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: "MockQueue", event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"},
        ),
    )
