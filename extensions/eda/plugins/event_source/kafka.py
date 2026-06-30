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
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

import aiohttp
import fastavro
import yaml
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context

if TYPE_CHECKING:
    from aiokafka.structs import ConsumerRecord

logger = logging.getLogger(__name__)

DOCUMENTATION = r"""
---
short_description: Receive events via a kafka topic.
description:
  - An ansible-rulebook event source plugin for receiving events via a kafka topic.
  - Each event includes C(meta.source_offset) set to C({topic}:{partition}:{offset})
    for tracing messages back to their Kafka coordinates.
  - Each event is assigned a valid RFC 4122 UUID under meta.uuid.
  - By default, a deterministic UUID5 is generated from the Kafka message
    coordinates (topic, partition, offset).
  - You can override this by providing a valid UUID via the "message_uuid"
    header or the "message_uuid" field in the message body. Headers take
    precedence over body.
  - If a provided "message_uuid" is not a valid UUID, the generated UUID is
    used instead and the original value is preserved under meta.message_id.
  - Messages with a null value (Kafka tombstones) are skipped.
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
      - When set to V(json), messages are decoded as UTF-8 text and parsed as JSON (default behavior).
      - When set to V(avro), messages are deserialized using Apache Avro.
      - With Avro, the plugin first attempts to use a local schema file if O(avro_schema_file) is provided.
        If no local schema is configured, the plugin attempts to read the message as an Avro Object Container
        (self-describing format with embedded schema).
    type: str
    default: "json"
    choices: ["json", "avro"]
  avro_schema_file:
    description:
      - Path to a local Avro schema file (.avsc) used for deserializing Avro messages.
      - The schema file must be valid JSON containing an Avro schema definition.
      - Required when O(message_format) is V(avro) and messages are in raw Avro binary format
        (schemaless, without embedded schema).
      - Not needed if messages use the Avro Object Container format (self-describing)
        or if O(schema_registry_url) is configured.
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
      - Basic auth credentials for the Schema Registry in V(user:password) format.
      - Mutually exclusive with O(schema_registry_bearer_token) and O(schema_registry_oauth_client_id).
    type: str
  schema_registry_bearer_token:
    description:
      - Static bearer or JWT token for Schema Registry authentication.
      - Mutually exclusive with O(schema_registry_basic_auth) and O(schema_registry_oauth_client_id).
    type: str
  schema_registry_oauth_client_id:
    description:
      - OAuth 2.0 client ID for Schema Registry authentication (Client Credentials flow).
      - Requires O(schema_registry_oauth_client_secret) and O(schema_registry_oauth_token_url).
      - Mutually exclusive with O(schema_registry_basic_auth) and O(schema_registry_bearer_token).
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
      - When V(true), reuse the Kafka SSL settings (O(cafile), O(certfile), O(keyfile))
        for Schema Registry HTTPS connections.
      - Ignored when explicit O(schema_ssl_cafile), O(schema_ssl_certfile), or
        O(schema_ssl_keyfile) are provided.
    type: bool
    default: true
  schema_ssl_cafile:
    description:
      - CA certificate file for Schema Registry HTTPS connections.
      - When provided, overrides the Kafka O(cafile) for registry connections.
      - Required when the Schema Registry uses a different CA than the Kafka broker.
    type: str
  schema_ssl_certfile:
    description:
      - Client certificate file for mTLS with Schema Registry.
      - When provided, overrides the Kafka O(certfile) for registry connections.
    type: str
  schema_ssl_keyfile:
    description:
      - Client key file for mTLS with Schema Registry.
      - When provided, overrides the Kafka O(keyfile) for registry connections.
    type: str
  schema_ssl_password:
    description:
      - Password for the Schema Registry client key file.
      - When provided, overrides the Kafka O(password) for registry connections.
    type: str
notes:
  - C(fastavro) is used for Avro deserialization when O(message_format) is V(avro).
  - C(aiohttp) is required only when O(schema_registry_url) is configured.
  - >-
    When O(message_format) is V(avro), the plugin applies a deserialization
    fallback chain. B(1.) If O(schema_registry_url) is configured and the
    message contains a Schema Registry wire format header, the schema is
    fetched from the registry. B(2.) If O(avro_schema_file) is provided,
    the local schema is used. B(3.) Otherwise, the message is treated as
    an Avro Object Container Format (OCF) file with an embedded schema.
  - >-
    When using Avro Object Container Format (OCF) messages, do B(not)
    provide O(avro_schema_file). It will cause deserialization to fail
    because the fallback chain (step 2) cannot parse the OCF container header.
  - >-
    The Schema Registry integration is compatible with any registry that
    implements the Confluent Schema Registry REST API, including Confluent
    Platform, Confluent Cloud, Karapace, Redpanda, and Apicurio Registry
    (via its Confluent compatibility API at C(/apis/ccompat/v7)). It is
    B(not) compatible with AWS Glue Schema Registry, which uses a different
    18-byte wire format.
  - >-
    Schema Registry authentication methods are mutually exclusive. Configure at most
    one of O(schema_registry_basic_auth), O(schema_registry_bearer_token),
    or the OAuth 2.0 parameters (O(schema_registry_oauth_client_id),
    O(schema_registry_oauth_client_secret), O(schema_registry_oauth_token_url)).
    The plugin raises an error if more than one method is configured.
  - >-
    A custom EDA credential type for this plugin is included in the collection
    at C(extensions/eda/plugins/event_source/credential_types/kafka-avro/). It uses C(extra_vars) and C(file) injectors
    to securely manage Kafka, SSL, Avro, and Schema Registry parameters.
    The C(file) injector writes certificate and schema content to temporary
    files inside the Decision Environment at runtime; the C(eda.filename.<name>)
    Jinja variable resolves to the temporary file path.
  - >-
    For EDA credential type documentation, see
    U(https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_decisions/eda-credential-types).
  - >-
    When O(schema_registry_url) uses HTTPS and the registry certificate is signed
    by a private or internal CA, you must provide the CA certificate via
    O(schema_ssl_cafile) or install it in the Decision Environment's trust store.
    Without it, SSL verification will fail because the default system CA bundle
    does not include private CAs.
  - >-
    When using OAuth 2.0 authentication with a separate identity provider
    (Keycloak, Okta, Azure AD), the same O(schema_ssl_cafile) is used for both
    the OAuth token endpoint and the Schema Registry API. If they use different
    CAs, concatenate both CA certificates into a single PEM file.
seealso:
  - name: Apache Avro Specification
    description: The Apache Avro data serialization format specification, including Object Container Files.
    link: https://avro.apache.org/docs/1.12.0/specification/
  - name: Confluent Wire Format
    description: The Confluent Schema Registry wire format (magic byte + schema ID + Avro binary).
    link: https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html
  - name: Confluent Schema Registry REST API
    description: REST API reference for the Confluent Schema Registry.
    link: https://docs.confluent.io/platform/current/schema-registry/develop/api.html
  - name: fastavro Documentation
    description: Python library used for Avro serialization and deserialization.
    link: https://fastavro.readthedocs.io/
  - name: aiokafka Documentation
    description: Async Python client for Apache Kafka used by this plugin.
    link: https://aiokafka.readthedocs.io/
"""

EXAMPLES = r"""
# For complete rulebook examples with rules and credential injection,
# see extensions/eda/rulebooks/demo_avro-*.yml

# JSON messages (default behavior, no message_format needed)
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

# Avro with a local schema file (.avsc)
# Use when messages are raw Avro binary (no wire format header, no
# embedded schema). The schema file must be valid JSON containing an
# Avro schema definition.
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-avro-consumer"
    offset: "earliest"
    message_format: "avro"
    avro_schema_file: "/path/to/schema.avsc"

# Avro Object Container Format (self-describing messages)
# Each message carries its own embedded schema. No schema file or
# Schema Registry is needed — just set message_format to avro.
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-ocf-events"
    group_id: "eda-ocf-consumer"
    offset: "earliest"
    message_format: "avro"

# Avro with Schema Registry (no authentication)
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-consumer"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "http://localhost:8081"

# Schema Registry with Basic Auth
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-basic"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "https://registry.example.com:8081"
    schema_registry_basic_auth: "user:password"

# Schema Registry with Bearer Token
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-bearer"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "https://registry.example.com:8081"
    schema_registry_bearer_token: "my-bearer-token"

# Schema Registry with OAuth 2.0 Client Credentials
# The plugin acquires an access token from the token endpoint, caches it,
# and refreshes it automatically before expiry.
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-sr-oauth"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "https://registry.example.com:8081"
    schema_registry_oauth_client_id: "my-client-id"
    schema_registry_oauth_client_secret: "my-client-secret"
    schema_registry_oauth_token_url: "https://auth.example.com/oauth/token"
    schema_registry_oauth_scope: "registry:read"

# Schema Registry with SSL and dedicated registry certificates
# Use schema_ssl_* to provide separate certificates for the Schema Registry
# when it uses a different CA than the Kafka broker.
- ansible.eda.kafka:
    host: "kafka.example.com"
    port: "9093"
    topic: "avro-events"
    group_id: "eda-sr-ssl"
    offset: "earliest"
    security_protocol: "SSL"
    cafile: "/certs/kafka-ca.pem"
    certfile: "/certs/kafka-client.pem"
    keyfile: "/certs/kafka-client-key.pem"
    message_format: "avro"
    schema_registry_url: "https://registry.example.com:8081"
    schema_registry_ssl: true
    schema_ssl_cafile: "/certs/registry-ca.pem"
    schema_ssl_certfile: "/certs/registry-client.pem"
    schema_ssl_keyfile: "/certs/registry-client-key.pem"

# Schema Registry with Apicurio Registry (Confluent compatibility API)
- ansible.eda.kafka:
    host: "localhost"
    port: "9092"
    topic: "avro-events"
    group_id: "eda-apicurio"
    offset: "earliest"
    message_format: "avro"
    schema_registry_url: "https://apicurio.example.com:8080/apis/ccompat/v7"
    schema_registry_basic_auth: "user:password"
"""

MESSAGE_UUID_KEY = "message_uuid"
QUEUE_TIMEOUT = 120
_uuid_warning = {"emitted": False}


class SchemaRegistryAuthError(Exception):
    """Raised when Schema Registry returns 401/403 (permanent auth failure)."""

    def __init__(self, message: str, *, status: int) -> None:
        """Initialize with message and HTTP status code."""
        super().__init__(message)
        self.status = status


class AvroDeserializer:
    """Handles Avro message deserialization with local schema files and Schema Registry."""

    MAX_MESSAGE_SIZE = 1_048_576  # 1MB - prevents memory exhaustion
    _WIRE_FORMAT_MAGIC = 0
    _WIRE_FORMAT_HEADER_SIZE = 5
    _SCHEMA_CACHE_MAX_SIZE = 100
    _REGISTRY_MAX_RETRIES = 3
    _REGISTRY_RETRY_INITIAL_DELAY = 1.0
    _REGISTRY_RETRY_MAX_DELAY = 10.0
    _REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
    _REGISTRY_RETRY_BACKOFF_FACTOR = 2

    def __init__(
        self,
        *,  # keyword-only: prevents ambiguous boolean positional args (FBT001)
        avro_schema_file: str | dict[str, Any] | None = None,
        schema_registry_url: str | None = None,
        schema_registry_basic_auth: str | None = None,
        schema_registry_bearer_token: str | None = None,
        schema_registry_oauth_client_id: str | None = None,
        schema_registry_oauth_client_secret: str | None = None,
        schema_registry_oauth_token_url: str | None = None,
        schema_registry_oauth_scope: str | None = None,
        schema_registry_ssl: bool = True,
        schema_ssl_cafile: str | None = None,
        schema_ssl_certfile: str | None = None,
        schema_ssl_keyfile: str | None = None,
        schema_ssl_password: str | None = None,
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
            schema_ssl_cafile: CA file for SSL connections.
            schema_ssl_certfile: Client certificate file for SSL.
            schema_ssl_keyfile: Client key file for SSL.
            schema_ssl_password: Password for encrypted keyfiles.

        Raises:
            FileNotFoundError: If schema file does not exist.
            ValueError: If configuration is invalid.

        """
        self._schema: dict[str, Any] | None = None

        # Schema Registry state
        self._registry_url = schema_registry_url
        # mypy no-any-return: typed values to match return type
        self._schema_cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
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
            if isinstance(avro_schema_file, dict):
                self._schema = fastavro.parse_schema(avro_schema_file)
                logger.info("Loaded Avro schema from inline definition")
            else:
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
                ssl_cafile=schema_ssl_cafile,
                ssl_certfile=schema_ssl_certfile,
                ssl_keyfile=schema_ssl_keyfile,
                ssl_password=schema_ssl_password,
            )

    def _configure_registry(  # pylint: disable=too-many-locals
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
        ssl_password: str | None,
    ) -> None:
        """Validate and configure Schema Registry connection."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            msg = "schema_registry_url must use http or https scheme"
            raise ValueError(msg)
        if not parsed.hostname:
            msg = "schema_registry_url must have a hostname"
            raise ValueError(msg)

        # Strip userinfo (user:password@) from URL before logging
        safe_url = parsed._replace(
            netloc=parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
        ).geturl()

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
            self._basic_auth_header = (
                f"Basic {base64.b64encode(basic_auth.encode()).decode()}"
            )

        # Build SSL context
        if use_ssl and parsed.scheme == "https":
            self._ssl_context = ssl.create_default_context()
            if ssl_cafile:
                self._ssl_context.load_verify_locations(ssl_cafile)
            else:
                logger.warning(
                    "Schema Registry URL uses HTTPS but no CA certificate was "
                    "provided (schema_ssl_cafile). The system CA trust store "
                    "will be used. If the registry certificate is signed by a "
                    "private CA, SSL verification will fail.",
                )
            if ssl_certfile and ssl_keyfile:
                self._ssl_context.load_cert_chain(
                    certfile=ssl_certfile,
                    keyfile=ssl_keyfile,
                    password=ssl_password,
                )

        logger.info("Schema Registry configured: %s", safe_url)

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
                    timeout=self._REQUEST_TIMEOUT,
                ) as resp:
                    resp.raise_for_status()
                    token_data = await resp.json()
                    self._oauth_access_token = token_data["access_token"]
                    self._oauth_token_expiry = (
                        time.time() + token_data.get("expires_in", 3600) - 30
                    )
                    logger.info("OAuth token obtained successfully")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("Failed to obtain OAuth token")
            if self._oauth_access_token is None:
                msg = (
                    "Initial OAuth token acquisition failed. "
                    "Check schema_registry_oauth_token_url, "
                    "client_id, and client_secret."
                )
                raise RuntimeError(msg) from exc
            logger.warning(
                "Using existing OAuth token (expires in %.0f seconds)",
                max(0, self._oauth_token_expiry - time.time()),
            )

    def _is_wire_format(self, data: bytes) -> bool:
        """Check if data starts with the Confluent wire format header."""
        return (
            self._registry_url is not None
            and len(data) >= self._WIRE_FORMAT_HEADER_SIZE
            and data[0] == self._WIRE_FORMAT_MAGIC
        )

    def _extract_schema_id(self, data: bytes) -> int:
        """Extract schema ID from Confluent wire format header."""
        (schema_id,) = struct.unpack(">I", data[1 : self._WIRE_FORMAT_HEADER_SIZE])
        return int(schema_id)

    async def _get_schema_from_registry(
        self,
        schema_id: int,
        session: aiohttp.ClientSession,
    ) -> dict[str, Any] | None:
        """Fetch and cache a schema from the Schema Registry by ID.

        Returns the parsed schema on success, None for permanent failures
        (schema not found, malformed response). Re-raises transient failures
        (network errors, auth errors, server errors) so the caller can
        decide whether to fall back or stop.

        Raises:
            SchemaRegistryAuthError: On HTTP 401/403 (authentication failure).
            aiohttp.ClientResponseError: On non-404/non-auth HTTP errors (server).
            aiohttp.ClientError: On network/connection errors.
            asyncio.TimeoutError: On request timeout.

        """
        url = f"{self._registry_url}/schemas/ids/{schema_id}"
        headers = await self._get_auth_headers()

        try:
            async with session.get(
                url,
                headers=headers,
                ssl=self._ssl_context,
                timeout=self._REQUEST_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                resp_data = await resp.json()
                schema_str = resp_data["schema"]
                # cast: fastavro lacks type stubs (mypy no-any-return)
                schema = fastavro.parse_schema(json.loads(schema_str))
                parsed_schema = cast("dict[str, Any]", schema)
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                logger.exception(
                    "Schema ID %d not found in registry (404)",
                    schema_id,
                )
                return None
            if exc.status in (
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
            ):
                if self._oauth_client_id:
                    msg = (
                        "Schema Registry authentication failed (HTTP %d) "
                        "— OAuth token may have expired. Check "
                        "oauth_token_url and credentials."
                    )
                else:
                    msg = (
                        "Schema Registry authentication failed (HTTP %d), "
                        "stopping plugin"
                    )
                logger.exception(msg, exc.status)
                raise SchemaRegistryAuthError(
                    msg % exc.status,
                    status=exc.status,
                ) from exc
            logger.exception(
                "Registry HTTP error %d for schema ID %d",
                exc.status,
                schema_id,
            )
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError):
            logger.exception(
                "Registry connection error for schema ID %d",
                schema_id,
            )
            raise
        except (KeyError, json.JSONDecodeError):
            logger.exception(
                "Malformed registry response for schema ID %d",
                schema_id,
            )
            return None

        # Evict oldest if cache is full
        if len(self._schema_cache) >= self._SCHEMA_CACHE_MAX_SIZE:
            self._schema_cache.popitem(last=False)

        self._schema_cache[schema_id] = parsed_schema
        logger.info("Cached schema ID %d from registry", schema_id)
        return parsed_schema

    async def _get_schema_with_retry(
        self,
        schema_id: int,
    ) -> dict[str, Any] | None:
        """Fetch schema from registry with exponential backoff on transient errors.

        Raises:
            SchemaRegistryAuthError: On HTTP 401/403 (propagated immediately).

        """
        if schema_id in self._schema_cache:
            self._schema_cache.move_to_end(schema_id)
            return self._schema_cache[schema_id]

        last_exc: Exception | None = None
        delay = self._REGISTRY_RETRY_INITIAL_DELAY

        # ruff: disable[PERF203]
        async with aiohttp.ClientSession() as session:
            for attempt in range(1, self._REGISTRY_MAX_RETRIES + 1):
                try:
                    return await self._get_schema_from_registry(
                        schema_id,
                        session,
                    )
                except SchemaRegistryAuthError:  # pylint: disable=try-except-raise
                    raise
                except (
                    aiohttp.ClientResponseError,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                ) as exc:
                    last_exc = exc
                    if attempt < self._REGISTRY_MAX_RETRIES:
                        logger.warning(
                            "Registry fetch failed for schema ID %d "
                            "(attempt %d/%d), retrying in %.1fs: %s",
                            schema_id,
                            attempt,
                            self._REGISTRY_MAX_RETRIES,
                            delay,
                            exc,
                        )
                        await asyncio.sleep(delay)
                        delay = min(
                            delay * self._REGISTRY_RETRY_BACKOFF_FACTOR,
                            self._REGISTRY_RETRY_MAX_DELAY,
                        )
        # ruff: enable[PERF203]

        logger.error(
            "Registry fetch failed for schema ID %d after %d attempts, "
            "skipping message: %s",
            schema_id,
            self._REGISTRY_MAX_RETRIES,
            last_exc,
        )
        return None

    def _load_schema_file(self, schema_path: str) -> None:
        """Load and validate a local Avro schema file."""
        resolved = Path(schema_path).expanduser().resolve()

        with resolved.open(encoding="utf-8") as f:
            raw_schema = yaml.safe_load(f)

        if not isinstance(raw_schema, dict):
            msg = (
                f"Avro schema must be a JSON object, "
                f"got {type(raw_schema).__name__}"
            )
            raise TypeError(msg)

        self._schema = fastavro.parse_schema(raw_schema)
        logger.info("Loaded Avro schema from %s", resolved)

    async def deserialize(self, data: bytes) -> dict[str, Any] | None:
        """Deserialize Avro binary data.

        Attempts deserialization in priority order:
        1. Wire format (Schema Registry) if schema_registry_url is configured
           and message has the magic byte header. If avro_schema_file is also
           configured, it is used as the reader schema for Avro schema
           evolution (defaults filled in for new fields, extra fields dropped).
        2. Local schema (schemaless_reader) if avro_schema_file was provided.
           If a wire format header was detected in step 1 but the registry
           lookup failed, the 5-byte header is stripped before falling back
           to the local schema.
        3. Object Container format (self-describing, embedded schema).

        Args:
            data: Raw bytes from a Kafka message value.

        Returns:
            Deserialized dict or None on failure.

        """
        if len(data) > self.MAX_MESSAGE_SIZE:
            logger.warning(
                "Message size %d exceeds limit %d, skipping",
                len(data),
                self.MAX_MESSAGE_SIZE,
            )
            return None

        payload = data  # default: entire message is the payload

        # Attempt 1: Wire format (Schema Registry)
        # SchemaRegistryAuthError (401/403) propagates uncaught
        # to terminate the plugin — auth failures are permanent.
        if self._is_wire_format(data):
            schema_id = self._extract_schema_id(data)
            registry_schema = await self._get_schema_with_retry(schema_id)

            if registry_schema is not None:
                return self._deserialize_with_schema(
                    data[self._WIRE_FORMAT_HEADER_SIZE :],
                    registry_schema,
                    self._schema,
                )
            # Registry unavailable or schema not found — fall through
            logger.warning(
                "Registry lookup failed for schema ID %d; falling back "
                "to local schema.",
                schema_id,
            )
            payload = data[self._WIRE_FORMAT_HEADER_SIZE :]

        # Attempt 2: Schemaless deserialization with local schema
        if self._schema is not None:
            return self._deserialize_with_schema(payload, self._schema)

        # Attempt 3: Object Container format (self-describing)
        return self._deserialize_object_container(data)

    def _deserialize_with_schema(
        self,
        data: bytes,
        writer_schema: dict[str, Any],
        reader_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Deserialize raw Avro binary using a provided schema.

        When reader_schema is provided, fastavro performs Avro schema
        resolution: fields present in the reader but missing from the
        writer are filled with their default values, and fields in the
        writer but absent from the reader are silently dropped.
        """
        reader = io.BytesIO(data)
        try:
            record = fastavro.schemaless_reader(reader, writer_schema, reader_schema)
        except (
            ValueError,
            KeyError,
            IndexError,
            UnicodeDecodeError,
            RuntimeError,
            EOFError,
            struct.error,
        ):
            logger.exception("Failed to deserialize Avro message with schema")
            return None
        if isinstance(record, dict):
            return record
        return {"value": record}

    def _deserialize_object_container(self, data: bytes) -> dict[str, Any] | None:
        """Deserialize Avro Object Container format (embedded schema).

        Returns the first record only. Kafka messages are single-value;
        additional records in a multi-record container are ignored.
        """
        reader = io.BytesIO(data)
        first_record = None
        try:
            avro_reader = fastavro.reader(reader)
            for i, record in enumerate(avro_reader):
                if i == 0:
                    first_record = (
                        record if isinstance(record, dict) else {"value": record}
                    )
                else:
                    logger.debug(
                        "Ignoring additional record(s) in Object Container message",
                    )
                    break
        except (
            ValueError,
            KeyError,
            IndexError,
            UnicodeDecodeError,
            RuntimeError,
            EOFError,
            struct.error,
        ):
            logger.exception(
                "Failed to deserialize Avro message as Object Container format",
            )
            return None
        return first_record


def _configure_avro(
    message_format: str,
    *,
    avro_schema_file: str | None = None,
    schema_registry_url: str | None = None,
    schema_registry_ssl: bool = True,
    schema_registry_basic_auth: str | None = None,
    schema_registry_bearer_token: str | None = None,
    schema_registry_oauth_client_id: str | None = None,
    schema_registry_oauth_client_secret: str | None = None,
    schema_registry_oauth_token_url: str | None = None,
    schema_registry_oauth_scope: str | None = None,
    schema_ssl_cafile: str | None = None,
    schema_ssl_certfile: str | None = None,
    schema_ssl_keyfile: str | None = None,
    schema_ssl_password: str | None = None,
) -> tuple[str, AvroDeserializer | None]:
    """Validate and configure Avro deserialization from plugin args."""
    deserializer = None
    if message_format == "avro":
        deserializer = AvroDeserializer(
            avro_schema_file=avro_schema_file,
            schema_registry_url=schema_registry_url,
            schema_registry_basic_auth=schema_registry_basic_auth,
            schema_registry_bearer_token=schema_registry_bearer_token,
            schema_registry_oauth_client_id=schema_registry_oauth_client_id,
            schema_registry_oauth_client_secret=schema_registry_oauth_client_secret,
            schema_registry_oauth_token_url=schema_registry_oauth_token_url,
            schema_registry_oauth_scope=schema_registry_oauth_scope,
            schema_registry_ssl=schema_registry_ssl,
            schema_ssl_cafile=schema_ssl_cafile if schema_registry_ssl else None,
            schema_ssl_certfile=schema_ssl_certfile if schema_registry_ssl else None,
            schema_ssl_keyfile=schema_ssl_keyfile if schema_registry_ssl else None,
            schema_ssl_password=schema_ssl_password if schema_registry_ssl else None,
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
    message_format = args.get("message_format", "json")
    if message_format not in ("json", "avro"):
        msg = f"Invalid message_format: {message_format}. Must be 'json' or 'avro'."
        raise ValueError(msg)

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
        "message_format": message_format,
        "avro_schema_file": args.get("avro_schema_file"),
        "schema_registry_url": args.get("schema_registry_url"),
        "schema_registry_ssl": args.get("schema_registry_ssl", True),
        "schema_registry_basic_auth": args.get("schema_registry_basic_auth"),
        "schema_registry_bearer_token": args.get("schema_registry_bearer_token"),
        "schema_registry_oauth_client_id": args.get(
            "schema_registry_oauth_client_id",
        ),
        "schema_registry_oauth_client_secret": args.get(
            "schema_registry_oauth_client_secret",
        ),
        "schema_registry_oauth_token_url": args.get(
            "schema_registry_oauth_token_url",
        ),
        "schema_registry_oauth_scope": args.get("schema_registry_oauth_scope"),
        "schema_ssl_cafile": args.get("schema_ssl_cafile"),
        "schema_ssl_certfile": args.get("schema_ssl_certfile"),
        "schema_ssl_keyfile": args.get("schema_ssl_keyfile"),
        "schema_ssl_password": args.get("schema_ssl_password"),
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


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid RFC 4122 UUID."""
    try:
        uuid.UUID(value)
        return True  # noqa: TRY300
    except (ValueError, AttributeError):
        return False


async def main(
    queue: asyncio.Queue[Any],
    args: dict[str, Any],
) -> None:
    """Receive events via a kafka topic."""
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
        message_format=config["message_format"],
        avro_schema_file=config["avro_schema_file"],
        schema_registry_url=config["schema_registry_url"],
        schema_registry_ssl=config["schema_registry_ssl"],
        schema_registry_basic_auth=config["schema_registry_basic_auth"],
        schema_registry_bearer_token=config["schema_registry_bearer_token"],
        schema_registry_oauth_client_id=config["schema_registry_oauth_client_id"],
        schema_registry_oauth_client_secret=config[
            "schema_registry_oauth_client_secret"
        ],
        schema_registry_oauth_token_url=config["schema_registry_oauth_token_url"],
        schema_registry_oauth_scope=config["schema_registry_oauth_scope"],
        schema_ssl_cafile=config["schema_ssl_cafile"] or config["cafile"],
        schema_ssl_certfile=config["schema_ssl_certfile"] or config["certfile"],
        schema_ssl_keyfile=config["schema_ssl_keyfile"] or config["keyfile"],
        schema_ssl_password=config["schema_ssl_password"] or config["password"],
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


async def _decode_message_body(
    msg_value: bytes | None,
    encoding: str,
    message_format: str,
    deserializer: AvroDeserializer | None,
) -> dict[str, Any] | str | None:
    """Decode a Kafka message body based on the configured format.

    Returns None for tombstone messages (null value) and deserialization failures.
    """
    if msg_value is None:
        logger.debug("Received tombstone message (null value), skipping")
        return None

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


def _process_event_uuid(
    msg: ConsumerRecord,
    headers: dict[str, str],
    data: dict[str, Any] | str | None,
    event: dict[str, Any],
) -> None:
    """Process the event UUID from headers, body, or Kafka coordinates.

    Priority: header message_uuid > body message_uuid > generated UUID5.
    If a provided message_uuid is not a valid UUID, the generated UUID is
    used and the original value is preserved under event.meta.message_id.
    """
    event_uuid = str(
        uuid.uuid5(
            uuid.NAMESPACE_OID,
            f"{msg.topic}:{msg.partition}:{msg.offset}",
        ),
    )

    message_id = None
    if MESSAGE_UUID_KEY in headers:
        message_id = headers[MESSAGE_UUID_KEY]
    elif isinstance(data, dict) and MESSAGE_UUID_KEY in data:
        message_id = data[MESSAGE_UUID_KEY]

    if message_id:
        if is_valid_uuid(message_id):
            event_uuid = message_id
        else:
            # If not a valid UUID, we must warn the user and use
            # the generated UUID instead. The original UUID is copied to
            # event.meta.message_id for tracking purposes.
            event["meta"]["message_id"] = message_id
            if not _uuid_warning["emitted"]:
                _uuid_warning["emitted"] = True
                logger.warning(
                    "Provided message_uuid is not a valid UUID,"
                    " using generated UUID. The original value has been"
                    " stored under event.meta.message_id for tracking.",
                )

    event["meta"]["uuid"] = event_uuid


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
    async for msg in kafka_consumer:
        event: dict[str, Any] = {
            "meta": {
                "source_offset": f"{msg.topic}:{msg.partition}:{msg.offset}",
                "produced_at": get_message_timestamp(msg),
            },
        }

        # Process headers
        headers: dict[str, str] = {}
        try:
            headers = {header[0]: header[1].decode(encoding) for header in msg.headers}
            event["meta"]["headers"] = headers
        except UnicodeError:
            logger.exception("Unicode error while decoding headers")

        data = await _decode_message_body(
            msg.value,
            encoding,
            message_format,
            deserializer,
        )

        # Process event UUID
        _process_event_uuid(msg, headers, data, event)

        # Add data to the event and put it into the queue
        if data:
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
