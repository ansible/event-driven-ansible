# pylint: disable=too-many-lines
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import ssl
import struct
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

import aiohttp
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

if TYPE_CHECKING:
    from aiokafka.structs import ConsumerRecord

try:
    import fastavro

    HAS_FASTAVRO = True
except ImportError:
    HAS_FASTAVRO = False

DOCUMENTATION = r"""
---
short_description: Receive events via a kafka topic.
description:
  - An ansible-rulebook event source plugin for receiving events via a kafka topic.
  - To make each message unique you can either add message_uuid to the header or
  - add message_uuid to the message body
  - if both of these are missing we will use the {topic}:{partition}.{offset} to
  - make the unique message uuid
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
        the certificate's authenticity.
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
  feedback:
    type: bool
    default: false
    description:
      - Should the source plugin wait for feedback before
        processing the next event from the kafka topic.
        This flag allows ansible rulebook to pass in an asyncio
        queue which is passed in the O(eda_feedback_queue).
        The source plugin should wait for the response to come
        back on this queue before it picks the next event from
        Kafka topic.
  feedback_timeout:
    type: int
    default: 120
    description:
      - Timeout in seconds to wait for feedback from the rule engine
        before raising an exception. Only applies when feedback is enabled.
  message_format:
    description:
      - The deserialization format for Kafka message values.
      - When set to C(json), messages are decoded as UTF-8 text and parsed as JSON (default behavior).
      - When set to C(avro), messages are deserialized using Apache Avro.
        Requires the C(fastavro) Python package to be installed.
      - With Avro, the plugin first attempts to use a local schema file if C(avro_schema_file) is provided.
        If no local schema is configured, the plugin attempts to read the message as an Avro Object Container
        (self-describing format with embedded schema).
    type: str
    default: "json"
    choices: ["json", "avro"]
  avro_schema_file:
    description:
      - Path to a local Avro schema file (.avsc) used for deserializing Avro messages.
      - The schema file must be valid JSON containing an Avro schema definition.
      - Required when C(message_format) is C(avro) and messages are in raw Avro binary format
        (schemaless, without embedded schema).
      - Not needed if messages use the Avro Object Container format (self-describing)
        or if C(schema_registry_url) is configured.
    type: str
  schema_registry_url:
    description:
      - URL of a Confluent-compatible Schema Registry (http or https).
      - When configured, the plugin auto-detects the Confluent wire format header
        in Avro messages and fetches schemas by ID from the registry.
      - Works with Confluent, Karapace, Apicurio (via /apis/ccompat/v7), and Redpanda.
      - Not compatible with AWS Glue Schema Registry (different wire format).
    type: str
  schema_registry_basic_auth:
    description:
      - Basic auth credentials for the Schema Registry in C(user:password) format.
      - Mutually exclusive with C(schema_registry_bearer_token) and C(schema_registry_oauth_client_id).
    type: str
  schema_registry_bearer_token:
    description:
      - Static bearer or JWT token for Schema Registry authentication.
      - Mutually exclusive with C(schema_registry_basic_auth) and C(schema_registry_oauth_client_id).
    type: str
  schema_registry_oauth_client_id:
    description:
      - OAuth 2.0 client ID for Schema Registry authentication (Client Credentials flow).
      - Requires C(schema_registry_oauth_client_secret) and C(schema_registry_oauth_token_url).
      - Mutually exclusive with C(schema_registry_basic_auth) and C(schema_registry_bearer_token).
    type: str
  schema_registry_oauth_client_secret:
    description:
      - OAuth 2.0 client secret for Schema Registry authentication.
    type: str
  schema_registry_oauth_token_url:
    description:
      - OAuth 2.0 token endpoint URL for obtaining access tokens.
    type: str
  schema_registry_oauth_scope:
    description:
      - OAuth 2.0 scope to request when obtaining access tokens.
    type: str
  schema_registry_ssl:
    description:
      - When C(true), reuse the Kafka SSL settings (C(cafile), C(certfile), C(keyfile))
        for Schema Registry HTTPS connections.
    type: bool
    default: true
notes:
  - >-
    A custom EDA credential type for this plugin is available as a GitHub Gist
    at U(<GIST_URL_PLACEHOLDER>). It uses C(extra_vars) and C(file) injectors
    to securely manage Kafka, SSL, Avro, and Schema Registry parameters.
  - >-
    For EDA credential type documentation, see
    U(https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_decisions/eda-credential-types).
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

- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-avro-consumer"
    offset: "earliest"
    message_format: "avro"
    avro_schema_file: "/path/to/schema.avsc"

- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-consumer"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "http://localhost:8081"

- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-auth"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "https://registry.example.com:8080/apis/ccompat/v7"
    schema_registry_basic_auth: "user:password"
"""

MESSAGE_UUID_KEY = "message_uuid"
QUEUE_TIMEOUT = 120


class AvroDeserializer:
    """Handles Avro message deserialization with local schema files and Schema Registry."""

    MAX_MESSAGE_SIZE = 1_048_576  # 1MB - prevents memory exhaustion
    _WIRE_FORMAT_MAGIC = 0
    _WIRE_FORMAT_HEADER_SIZE = 5
    _SCHEMA_CACHE_MAX_SIZE = 100

    def __init__(
        self,
        *,  # keyword-only: prevents ambiguous boolean positional args (FBT001)
        avro_schema_file: str | None = None,
        schema_registry_url: str | None = None,
        schema_registry_basic_auth: str | None = None,
        schema_registry_bearer_token: str | None = None,
        schema_registry_oauth_client_id: str | None = None,
        schema_registry_oauth_client_secret: str | None = None,
        schema_registry_oauth_token_url: str | None = None,
        schema_registry_oauth_scope: str | None = None,
        schema_registry_ssl: bool = True,
        ssl_cafile: str | None = None,
        ssl_certfile: str | None = None,
        ssl_keyfile: str | None = None,
    ) -> None:
        """Initialize with local schema file and/or Schema Registry config.

        Args:
            avro_schema_file: Path to a local .avsc schema file.
            schema_registry_url: Schema Registry URL (http/https).
            schema_registry_basic_auth: Basic auth credentials (user:password).
            schema_registry_bearer_token: Static bearer/JWT token.
            schema_registry_oauth_client_id: OAuth 2.0 client ID.
            schema_registry_oauth_client_secret: OAuth 2.0 client secret.
            schema_registry_oauth_token_url: OAuth 2.0 token endpoint URL.
            schema_registry_oauth_scope: OAuth 2.0 scope.
            schema_registry_ssl: Reuse Kafka SSL settings for Registry.
            ssl_cafile: CA file for SSL connections.
            ssl_certfile: Client certificate file for SSL.
            ssl_keyfile: Client key file for SSL.

        Raises:
            ImportError: If fastavro is not installed.
            FileNotFoundError: If schema file does not exist.
            ValueError: If configuration is invalid.

        """
        if not HAS_FASTAVRO:
            msg = (
                "The 'fastavro' package is required for Avro deserialization. "
                "Install it with: pip install fastavro"
            )
            raise ImportError(msg)

        self._logger = logging.getLogger()
        self._schema: dict[str, Any] | None = None

        # Schema Registry state
        self._registry_url = schema_registry_url
        # mypy no-any-return: typed values to match return type
        self._schema_cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
        self._http_session: aiohttp.ClientSession | None = None
        self._ssl_context: ssl.SSLContext | None = None

        # Auth state
        self._basic_auth_header: str | None = None
        self._bearer_token: str | None = schema_registry_bearer_token
        self._oauth_client_id = schema_registry_oauth_client_id
        self._oauth_client_secret = schema_registry_oauth_client_secret
        self._oauth_token_url = schema_registry_oauth_token_url
        self._oauth_scope = schema_registry_oauth_scope
        self._oauth_access_token: str | None = None
        self._oauth_token_expiry: float = 0.0

        if avro_schema_file:
            self._load_schema_file(avro_schema_file)

        if schema_registry_url:
            self._configure_registry(
                url=schema_registry_url,
                basic_auth=schema_registry_basic_auth,
                bearer_token=schema_registry_bearer_token,
                oauth_client_id=schema_registry_oauth_client_id,
                oauth_client_secret=schema_registry_oauth_client_secret,
                oauth_token_url=schema_registry_oauth_token_url,
                use_ssl=schema_registry_ssl,
                ssl_cafile=ssl_cafile,
                ssl_certfile=ssl_certfile,
                ssl_keyfile=ssl_keyfile,
            )

    def _configure_registry(
        self,
        *,
        url: str,
        basic_auth: str | None,
        bearer_token: str | None,
        oauth_client_id: str | None,
        oauth_client_secret: str | None,
        oauth_token_url: str | None,
        use_ssl: bool,
        ssl_cafile: str | None,
        ssl_certfile: str | None,
        ssl_keyfile: str | None,
    ) -> None:
        """Validate and configure Schema Registry connection."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            msg = f"schema_registry_url must use http or https scheme, got: {url}"
            raise ValueError(msg)
        if not parsed.hostname:
            msg = f"schema_registry_url must have a hostname, got: {url}"
            raise ValueError(msg)

        # Validate auth mutual exclusion
        auth_methods = sum(1 for a in (basic_auth, bearer_token, oauth_client_id) if a)
        if auth_methods > 1:
            msg = (
                "Only one Schema Registry auth method can be used at a time. "
                "Provide only one of: schema_registry_basic_auth, "
                "schema_registry_bearer_token, or schema_registry_oauth_client_id."
            )
            raise ValueError(msg)

        # Validate OAuth fields
        if oauth_client_id and not (oauth_client_secret and oauth_token_url):
            msg = (
                "schema_registry_oauth_client_secret and "
                "schema_registry_oauth_token_url are required when "
                "schema_registry_oauth_client_id is set."
            )
            raise ValueError(msg)

        # Build Basic Auth header
        if basic_auth:
            creds = base64.b64encode(basic_auth.encode()).decode()
            self._basic_auth_header = f"Basic {creds}"

        # Build SSL context
        if use_ssl and parsed.scheme == "https":
            self._ssl_context = ssl.create_default_context()
            if ssl_cafile:
                self._ssl_context.load_verify_locations(ssl_cafile)
            if ssl_certfile and ssl_keyfile:
                self._ssl_context.load_cert_chain(
                    certfile=ssl_certfile,
                    keyfile=ssl_keyfile,
                )

        self._logger.info("Schema Registry configured: %s", url)

    async def _get_auth_headers(self) -> dict[str, str]:
        """Build authorization headers for Schema Registry requests."""
        headers: dict[str, str] = {
            "Accept": "application/vnd.schemaregistry.v1+json",
        }
        if self._basic_auth_header:
            headers["Authorization"] = self._basic_auth_header
        elif self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        elif self._oauth_client_id:
            if time.time() >= self._oauth_token_expiry:
                await self._fetch_oauth_token()
            if self._oauth_access_token:
                headers["Authorization"] = f"Bearer {self._oauth_access_token}"
        return headers

    async def _fetch_oauth_token(self) -> None:
        """Obtain or refresh an OAuth 2.0 access token."""
        if not self._oauth_token_url:
            return
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self._oauth_client_id,
                    "client_secret": self._oauth_client_secret,
                }
                if self._oauth_scope:
                    data["scope"] = self._oauth_scope
                async with session.post(
                    self._oauth_token_url,
                    data=data,
                    ssl=self._ssl_context,
                ) as resp:
                    resp.raise_for_status()
                    token_data = await resp.json()
                    self._oauth_access_token = token_data["access_token"]
                    self._oauth_token_expiry = (
                        time.time() + token_data.get("expires_in", 3600) - 30
                    )
                    self._logger.info("OAuth token obtained successfully")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.exception("Failed to obtain OAuth token")
            if self._oauth_access_token is None:
                msg = (
                    "Initial OAuth token acquisition failed. "
                    "Check schema_registry_oauth_token_url, "
                    "client_id, and client_secret."
                )
                raise RuntimeError(msg) from exc
            self._logger.warning(
                "Using existing OAuth token (expires in %.0f seconds)",
                max(0, self._oauth_token_expiry - time.time()),
            )

    def _is_wire_format(self, data: bytes) -> bool:
        """Check if data starts with the Confluent wire format header."""
        return (
            self._registry_url is not None
            and len(data) > self._WIRE_FORMAT_HEADER_SIZE
            and data[0] == self._WIRE_FORMAT_MAGIC
        )

    def _extract_schema_id(self, data: bytes) -> int:
        """Extract schema ID from Confluent wire format header."""
        (schema_id,) = struct.unpack(">I", data[1 : self._WIRE_FORMAT_HEADER_SIZE])
        return int(schema_id)

    async def _get_schema_from_registry(self, schema_id: int) -> dict[str, Any] | None:
        """Fetch and cache a schema from the Schema Registry by ID."""
        # Check cache
        if schema_id in self._schema_cache:
            self._schema_cache.move_to_end(schema_id)
            return self._schema_cache[schema_id]

        # Fetch from registry
        url = f"{self._registry_url}/schemas/ids/{schema_id}"
        headers = await self._get_auth_headers()

        try:
            if self._http_session is None or self._http_session.closed:
                self._http_session = aiohttp.ClientSession()

            async with self._http_session.get(
                url,
                headers=headers,
                ssl=self._ssl_context,
            ) as resp:
                resp.raise_for_status()
                resp_data = await resp.json()
                schema_str = resp_data["schema"]
                # cast: fastavro lacks type stubs (mypy no-any-return)
                schema = fastavro.parse_schema(json.loads(schema_str))
                parsed_schema = cast("dict[str, Any]", schema)
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.exception(
                "Failed to fetch schema ID %d from registry",
                schema_id,
            )
            return None

        # Evict oldest if cache is full
        if len(self._schema_cache) >= self._SCHEMA_CACHE_MAX_SIZE:
            self._schema_cache.popitem(last=False)

        self._schema_cache[schema_id] = parsed_schema
        self._logger.info("Cached schema ID %d from registry", schema_id)
        return parsed_schema

    def _load_schema_file(self, schema_path: str) -> None:
        """Load and validate a local Avro schema file."""
        # pathlib over os.path (PTH111/PTH113)
        resolved = Path(schema_path).expanduser().resolve()

        if not resolved.is_file():
            msg = f"Avro schema file not found: {resolved}"
            raise FileNotFoundError(msg)

        with resolved.open(encoding="utf-8") as f:
            raw_schema = json.load(f)

        self._schema = fastavro.parse_schema(raw_schema)
        self._logger.info("Loaded Avro schema from %s", resolved)

    async def deserialize(self, data: bytes) -> dict[str, Any] | None:
        """Deserialize Avro binary data.

        Attempts deserialization in priority order:
        1. Wire format (Schema Registry) if schema_registry_url is configured
           and message has the magic byte header.
        2. Local schema (schemaless_reader) if avro_schema_file was provided.
        3. Object Container format (self-describing, embedded schema).

        Args:
            data: Raw bytes from a Kafka message value.

        Returns:
            Deserialized dict or None on failure.

        """
        if len(data) > self.MAX_MESSAGE_SIZE:
            self._logger.warning(
                "Message size %d exceeds limit %d, skipping",
                len(data),
                self.MAX_MESSAGE_SIZE,
            )
            return None

        # Attempt 1: Wire format (Schema Registry)
        if self._is_wire_format(data):
            schema_id = self._extract_schema_id(data)
            registry_schema = await self._get_schema_from_registry(schema_id)
            if registry_schema is not None:
                return self._deserialize_with_schema(
                    data[self._WIRE_FORMAT_HEADER_SIZE :],
                    registry_schema,
                )
            self._logger.warning(
                "Registry lookup failed for schema ID %d, trying fallbacks",
                schema_id,
            )

        # Attempt 2: Schemaless deserialization with local schema
        if self._schema is not None:
            return self._deserialize_with_schema(data, self._schema)

        # Attempt 3: Object Container format (self-describing)
        return self._deserialize_object_container(data)

    def _deserialize_with_schema(
        self,
        data: bytes,
        schema: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Deserialize raw Avro binary using a provided schema."""
        try:  # pylint: disable=no-else-return
            reader = io.BytesIO(data)
            record = fastavro.schemaless_reader(reader, schema)
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.exception("Failed to deserialize Avro message with schema")
            return None
        else:  # TRY300: scope except to fastavro only
            if isinstance(record, dict):
                return record
            return {"value": record}

    def _deserialize_object_container(self, data: bytes) -> dict[str, Any] | None:
        """Deserialize Avro Object Container format (embedded schema)."""
        try:
            reader = io.BytesIO(data)
            avro_reader = fastavro.reader(reader)
            for record in avro_reader:
                if isinstance(record, dict):
                    return record
                return {"value": record}
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.exception(
                "Failed to deserialize Avro message as Object Container format",
            )
        return None

    async def close(self) -> None:
        """Close the HTTP session if open."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()


def _configure_avro(
    args: dict[str, Any],
    ssl_cafile: str | None = None,
    ssl_certfile: str | None = None,
    ssl_keyfile: str | None = None,
) -> tuple[str, AvroDeserializer | None]:
    """Validate and configure Avro deserialization from plugin args."""
    logger = logging.getLogger()
    message_format = args.get("message_format", "json")
    avro_schema_file = args.get("avro_schema_file")

    if message_format not in ("json", "avro"):
        msg = f"Invalid message_format: {message_format}. Must be 'json' or 'avro'."
        raise ValueError(msg)

    deserializer = None
    if message_format == "avro":
        schema_registry_ssl = args.get("schema_registry_ssl", True)
        deserializer = AvroDeserializer(
            avro_schema_file=avro_schema_file,
            schema_registry_url=args.get("schema_registry_url"),
            schema_registry_basic_auth=args.get("schema_registry_basic_auth"),
            schema_registry_bearer_token=args.get("schema_registry_bearer_token"),
            schema_registry_oauth_client_id=args.get("schema_registry_oauth_client_id"),
            schema_registry_oauth_client_secret=args.get(
                "schema_registry_oauth_client_secret",
            ),
            schema_registry_oauth_token_url=args.get("schema_registry_oauth_token_url"),
            schema_registry_oauth_scope=args.get("schema_registry_oauth_scope"),
            schema_registry_ssl=schema_registry_ssl,
            ssl_cafile=ssl_cafile if schema_registry_ssl else None,
            ssl_certfile=ssl_certfile if schema_registry_ssl else None,
            ssl_keyfile=ssl_keyfile if schema_registry_ssl else None,
        )
        logger.info("Avro deserialization enabled")

    return message_format, deserializer


def _validate_and_normalize_topics(args: dict[str, Any]) -> list[str] | None:
    """Validate and normalize topic configuration.

    Args:
        args: Plugin arguments

    Returns:
        List of topics or None if topic_pattern is used

    Raises:
        ValueError: If topic configuration is invalid

    """
    topic = args.get("topic")
    topics = args.get("topics")
    topic_pattern = args.get("topic_pattern")

    num_topics = sum(1 for tp in (topic, topics, topic_pattern) if tp is not None)
    if num_topics != 1:
        msg = "Exactly one of topic, topics, or topic_pattern must be provided."
        raise ValueError(msg)

    if topic:
        return [topic]
    return topics


def _parse_kafka_args(args: dict[str, Any]) -> dict[str, Any]:
    """Parse and extract Kafka configuration from args.

    Args:
        args: Plugin arguments

    Returns:
        Dictionary containing parsed Kafka configuration

    Raises:
        ValueError: If offset is invalid or the feedback options are invalid

    """
    offset = args.get("offset", "latest")
    if offset not in ("latest", "earliest"):
        msg = f"Invalid offset option: {offset}"
        raise ValueError(msg)

    feedback_enabled = args.get("feedback", False)
    eda_feedback_queue = args.get("eda_feedback_queue")

    if feedback_enabled and eda_feedback_queue is None:
        msg = (
            "feedback: true was set but no feedback queue was provided. "
            "This requires a compatible version of ansible-rulebook that "
            "supports the feedback mechanism."
        )
        raise ValueError(msg)

    if feedback_enabled:
        enable_auto_commit = False
    else:
        enable_auto_commit = True
        eda_feedback_queue = None

    return {
        "host": args.get("host"),
        "port": args.get("port"),
        "cafile": args.get("cafile"),
        "certfile": args.get("certfile"),
        "keyfile": args.get("keyfile"),
        "password": args.get("password"),
        "check_hostname": args.get("check_hostname", True),
        "verify_mode": args.get("verify_mode", "CERT_REQUIRED"),
        "group_id": args.get("group_id"),
        "offset": offset,
        "encoding": args.get("encoding", "utf-8"),
        "security_protocol": args.get("security_protocol", "PLAINTEXT"),
        "enable_auto_commit": enable_auto_commit,
        "eda_feedback_queue": eda_feedback_queue,
        "sasl_mechanism": args.get("sasl_mechanism", "PLAIN"),
        "sasl_plain_username": args.get("sasl_plain_username"),
        "sasl_plain_password": args.get("sasl_plain_password"),
        "sasl_kerberos_service_name": args.get("sasl_kerberos_service_name"),
        "sasl_kerberos_domain_name": args.get("sasl_kerberos_domain_name"),
        "metadata_max_age_ms": int(args.get("metadata_max_age_ms", 300000)),
        "feedback_timeout": int(args.get("feedback_timeout", QUEUE_TIMEOUT)),
    }


def _create_ssl_context(
    cafile: str | None,
    certfile: str | None,
    keyfile: str | None,
    password: str | None,
    *,
    check_hostname: bool,
    verify_mode_str: str,
    security_protocol: str,
) -> tuple[Any | None, str]:
    """Create SSL context if needed.

    Args:
        cafile: CA file path
        certfile: Certificate file path
        keyfile: Key file path
        password: Password for the key file
        check_hostname: Whether to check hostname
        verify_mode_str: Verification mode string
        security_protocol: Security protocol

    Returns:
        Tuple of (ssl_context, updated_security_protocol)

    Raises:
        ValueError: If verify_mode is invalid

    """
    verify_modes = {
        "CERT_NONE": CERT_NONE,
        "CERT_OPTIONAL": CERT_OPTIONAL,
        "CERT_REQUIRED": CERT_REQUIRED,
    }
    try:
        verify_mode = verify_modes[verify_mode_str]
    except KeyError as exc:
        msg = f"Invalid verify_mode option: {verify_mode_str}"
        raise ValueError(msg) from exc

    if not (cafile or certfile or keyfile or security_protocol.endswith("SSL")):
        return None, security_protocol

    security_protocol = security_protocol.replace("PLAINTEXT", "SSL")
    ssl_context = create_ssl_context(
        cafile=cafile,
        certfile=certfile,
        keyfile=keyfile,
        password=password,
    )
    ssl_context.check_hostname = check_hostname
    ssl_context.verify_mode = verify_mode
    return ssl_context, security_protocol


def get_message_timestamp(msg: ConsumerRecord) -> str:
    """Convert Kafka message timestamp to ISO 8601 format with Z suffix.

    Args:
        msg: Kafka ConsumerRecord containing timestamp in milliseconds

    Returns:
        ISO 8601 formatted timestamp string with Z suffix (e.g., "2024-02-23T18:57:44Z")

    """
    return (
        datetime.fromtimestamp(msg.timestamp / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


async def main(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
    logger = logging.getLogger()

    # Validate and normalize topics
    topics = _validate_and_normalize_topics(args)
    topic_pattern = args.get("topic_pattern")

    # Parse Kafka configuration
    config = _parse_kafka_args(args)

    # Create SSL context if needed
    ssl_context, security_protocol = _create_ssl_context(
        cafile=config["cafile"],
        certfile=config["certfile"],
        keyfile=config["keyfile"],
        password=config["password"],
        check_hostname=config["check_hostname"],
        verify_mode_str=config["verify_mode"],
        security_protocol=config["security_protocol"],
    )

    # Create Kafka consumer
    kafka_consumer = AIOKafkaConsumer(
        bootstrap_servers=f"{config['host']}:{config['port']}",
        group_id=config["group_id"],
        enable_auto_commit=config["enable_auto_commit"],
        max_poll_records=1,
        auto_offset_reset=config["offset"],
        security_protocol=security_protocol,
        ssl_context=ssl_context,
        sasl_mechanism=config["sasl_mechanism"],
        sasl_plain_username=config["sasl_plain_username"],
        sasl_plain_password=config["sasl_plain_password"],
        sasl_kerberos_service_name=config["sasl_kerberos_service_name"],
        sasl_kerberos_domain_name=config["sasl_kerberos_domain_name"],
        metadata_max_age_ms=config["metadata_max_age_ms"],
    )

    message_format, deserializer = _configure_avro(
        args,
        ssl_cafile=config["cafile"],
        ssl_certfile=config["certfile"],
        ssl_keyfile=config["keyfile"],
    )

    kafka_consumer.subscribe(topics=topics, pattern=topic_pattern)

    await kafka_consumer.start()

    try:
        await receive_msg(
            queue,
            kafka_consumer,
            config["encoding"],
            config["eda_feedback_queue"],
            config["feedback_timeout"],
            message_format,
            deserializer,
        )
    finally:
        logger.info("Stopping kafka consumer")
        await kafka_consumer.stop()
        if deserializer is not None:
            await deserializer.close()


async def _decode_message_body(
    msg_value: bytes,
    encoding: str,
    message_format: str,
    deserializer: AvroDeserializer | None,
) -> dict[str, Any] | str | None:
    """Decode a Kafka message body based on the configured format."""
    logger = logging.getLogger()

    if message_format == "avro" and deserializer is not None:
        data = await deserializer.deserialize(msg_value)
        if data is None:
            logger.warning("Avro deserialization returned None, skipping message")
        return data

    try:
        value = msg_value.decode(encoding)
        return cast("dict[str, Any]", json.loads(value))
    except json.decoder.JSONDecodeError:
        logger.info("JSON decode error, storing raw value")
        return value
    except UnicodeError:
        logger.exception("Unicode error while decoding message body")
        return None


async def receive_msg(
    queue: asyncio.Queue[Any],
    kafka_consumer: AIOKafkaConsumer,
    encoding: str,
    eda_feedback_queue: asyncio.Queue[Any] | None,
    feedback_timeout: int,
    message_format: str = "json",
    deserializer: AvroDeserializer | None = None,
) -> None:
    """Receive messages from the Kafka topic and put them into the queue."""
    logger = logging.getLogger()

    async for msg in kafka_consumer:
        event: dict[str, Any] = {
            "meta": {
                "source_offset": f"{msg.topic}:{msg.partition}:{msg.offset}",
                "produced_at": get_message_timestamp(msg),
            },
        }

        # Process headers
        try:
            headers: dict[str, str] = {
                header[0]: header[1].decode(encoding) for header in msg.headers
            }
            event["meta"]["headers"] = headers
            if MESSAGE_UUID_KEY in headers:
                event["meta"]["uuid"] = headers[MESSAGE_UUID_KEY]

        except UnicodeError:
            logger.exception("Unicode error while decoding headers")

        data = await _decode_message_body(
            msg.value,
            encoding,
            message_format,
            deserializer,
        )

        # Add data to the event and put it into the queue
        if data:
            if (
                MESSAGE_UUID_KEY not in event["meta"].get("headers", {})
                and isinstance(data, dict)
                and MESSAGE_UUID_KEY in data
            ):
                event["meta"]["uuid"] = data[MESSAGE_UUID_KEY]

            event["body"] = data
            await queue.put(event)
            if eda_feedback_queue:
                try:
                    await asyncio.wait_for(
                        eda_feedback_queue.get(),
                        timeout=feedback_timeout,
                    )
                    await kafka_consumer.commit()
                except asyncio.TimeoutError:
                    logger.exception("Timed out waiting for feedback")
                    raise

        await asyncio.sleep(0)


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue(asyncio.Queue[Any]):
        """A fake queue."""

        async def put(self: MockQueue, event: dict[str, Any]) -> None:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"topic": "eda", "host": "localhost", "port": "9092", "group_id": "test"},
        ),
    )
