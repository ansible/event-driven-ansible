"""
This module creates a Token Provider which gets called by
aiokafka when using SASL_OAUTHBEARER. There are 4 kinds
of Token Providers based on sasl_oauth_method
   ClientSecretBasic
   ClientSecretPost
   ClientSecretJwt
   PrivateKeyJwt

OAuth2TokenProvider is the abstract base class which gets tokens
from Authorization Server but requires different payloads to
be sent to the Server based on what the sub classes build




On the server side when this access token is validated using
the JWKS URL set the server only checks the access token
"""

import base64
import datetime
import hashlib
import logging
import time
import uuid
from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple, Union

import aiohttp
import cryptography
import jwt
from aiohttp import BasicAuth
from aiokafka.abc import AbstractTokenProvider
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate

JWT_BEARER_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
DEFAULT_JWT_DURATION = "30"
DEFAULT_ACCESS_TOKEN_EXPIRY = 1800
DEFAULT_ALGORITHM = "RS256"
GRANT_TYPE = "client_credentials"
CLIENT_SECRET_METHODS = [
    "client_secret_basic",
    "client_secret_post",
    "client_secret_jwt",
]
PRIVATE_KEY_METHODS = [
    "private_key_jwt",
]
VALID_OAUTH_METHODS = CLIENT_SECRET_METHODS + PRIVATE_KEY_METHODS

LOGGER = logging.getLogger()


class OAuth2TokenProvider(AbstractTokenProvider):  # type: ignore[misc]
    """
     Handles OAuth2 token acquisition and refresh for Auth Server

    This class handles the basic token retrieval but requires the
    the subclasses to provide what kind of payload is sent to
    the Auth Server.
    """

    def __init__(self, *_args: Any, **kwargs: Any) -> None:
        self.token_endpoint = kwargs["sasl_oauth_token_endpoint"]
        self.client_id = kwargs["sasl_oauth_client_id"]
        self.client_secret = kwargs.get("sasl_oauth_client_secret")
        self.scope = kwargs.get("sasl_oauth_scope")
        self.algorithm = kwargs.get("sasl_oauth_algorithm", DEFAULT_ALGORITHM)
        self.token_duration_in_minutes = int(
            kwargs.get("sasl_oauth_token_duration", DEFAULT_JWT_DURATION)
        )
        self.subject = kwargs.get("sasl_oauth_subject", self.client_id)
        self.issuer = kwargs.get("sasl_oauth_issuer", self.client_id)
        self.audience = kwargs.get("sasl_oauth_audience", self.token_endpoint)
        self.access_token = None
        self.token_expires_at = 0
        self.auth: Optional[BasicAuth] = None

    async def token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        current_time = time.time()

        # Check if token is still valid (with 5 min buffer)
        if self.access_token and current_time < (self.token_expires_at - 300):
            return self.access_token

        # Request new token from Enterprise OAuth2 server
        return await self._request_new_token()

    async def _request_new_token(self) -> str:
        """Request a new access token from Authorization Server"""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = self._create_payload()
        response_text = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_endpoint, headers=headers, data=data, auth=self.auth
                ) as response:
                    if response.ok:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        expires_in = token_data.get(
                            "expires_in", DEFAULT_ACCESS_TOKEN_EXPIRY
                        )
                        self.token_expires_at = time.time() + expires_in
                    else:
                        response_text = await response.text()
                        response.raise_for_status()

            LOGGER.debug("Successfully obtained OAuth2 token")
            return self.access_token  # type: ignore[return-value]

        except aiohttp.ClientError as e:
            LOGGER.error("Failed to obtain OAuth2 token: %s", str(e))
            LOGGER.error("Response text %s", str(response_text))
            raise
        except KeyError as e:
            LOGGER.error("Invalid token response format: %s", str(e))
            raise

    @abstractmethod
    def _create_payload(self) -> Dict[str, Any]:
        pass

    def _create_jwt_payload(self) -> Dict[str, Any]:
        return {
            "sub": self.subject,
            "iss": self.issuer,
            "aud": self.audience,
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(minutes=self.token_duration_in_minutes),
            "iat": datetime.datetime.utcnow(),
            "jti": str(uuid.uuid4()),
        }


class ClientSecretBasic(OAuth2TokenProvider):
    """
     Fetches access token using the client_secret_basic

    Defined in RFC 6749, sends the client secret and client id
    in the Authorization header
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.client_secret is not None:
            self.auth = BasicAuth(login=self.client_id, password=self.client_secret)
        else:
            raise ValueError("oauth_client_secret cannot be empty")

    def _create_payload(self) -> Dict[str, Any]:
        data = {"grant_type": GRANT_TYPE}

        if self.scope:
            data["scope"] = self.scope
        return data


class ClientSecretPost(OAuth2TokenProvider):
    """
    Fetches access token using the client_secret_post

    Defined in RFC 6749, sends the client secret and client id
    in the post body
    """

    def _create_payload(self) -> Dict[str, Any]:
        data = {
            "grant_type": GRANT_TYPE,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            data["scope"] = self.scope

        return data


class ClientSecretJwt(OAuth2TokenProvider):
    """
    Fetches access token using the client_secret_jwt

    Defined in RFC 7523, creates a JWT signs it with client secret
    The encoding happens using HS256 unlike RS256
    """

    def _create_payload(self) -> Dict[str, Any]:
        # Create the JWT header
        headers = {
            "alg": "HS256",
            "typ": "JWT",
            "kid": str(uuid.uuid4()),
        }

        encoded_jwt = jwt.encode(
            self._create_jwt_payload(),
            self.client_secret,
            algorithm="HS256",
            headers=headers,
        )

        data = {
            "grant_type": "client_credentials",
            "client_assertion": encoded_jwt,
            "client_id": self.client_id,
            "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
        }

        if self.scope:
            data["scope"] = self.scope
        return data


class PrivateKeyJwt(OAuth2TokenProvider):
    """
    Fetches access token using the private_key_jwt

    Defined in RFC 7523, creates a JWT signs it with client secret
    The encoding happens using RS256, some Auth Servers require
    the public key thumb print to be sent up in the JWT headers
    Private Key JWT is described in RFC7521 and RFC 7523.
    It's used in Kafka 4.1 as part of KIP 1139
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.private_keyfile = kwargs["sasl_oauth_private_keyfile"]
        self.public_keyfile = kwargs.get("sasl_oauth_public_keyfile")

    def _get_public_cert_thumbprint(self) -> Tuple[str, str]:
        with open(self.public_keyfile, encoding="utf-8") as f:  # type: ignore[arg-type]
            public_key = f.read()

        # Convert PEM to DER and load the certificate
        cert = load_pem_x509_certificate(public_key.encode("utf-8"), default_backend())
        der_certificate = cert.public_bytes(
            encoding=cryptography.hazmat.primitives.serialization.Encoding.DER
        )

        # Compute the SHA-1 hash
        sha1_hash = hashlib.sha1(der_certificate).digest()
        sha256_hash = hashlib.sha256(der_certificate).digest()

        # Base64url-encode the hash
        x5t_value = base64.urlsafe_b64encode(sha1_hash).decode("utf-8").rstrip("=")
        x5t_s256_value = (
            base64.urlsafe_b64encode(sha256_hash).decode("utf-8").rstrip("=")
        )
        return (x5t_value, x5t_s256_value)

    def _create_jwt_headers(self) -> Dict[str, Any]:
        # Create the JWT header
        headers = {
            "alg": self.algorithm,
            "typ": "JWT",
            "kid": str(uuid.uuid4()),
        }

        # some auth servers like MSFT will reject the token request
        # without the public key thumbprint.
        if self.public_keyfile:
            x5t_value, x5t_s256_value = self._get_public_cert_thumbprint()
            headers["x5t"] = x5t_value
            headers["x5t#S256"] = x5t_s256_value

        return headers

    def _create_payload(self) -> Dict[str, Any]:
        with open(self.private_keyfile, encoding="utf-8") as f:
            private_key = f.read()

        encoded_jwt = jwt.encode(
            self._create_jwt_payload(),
            private_key,
            algorithm=self.algorithm,
            headers=self._create_jwt_headers(),
        )

        data = {
            "grant_type": "client_credentials",
            "client_assertion": encoded_jwt,
            "client_id": self.client_id,
            "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
        }

        if self.scope:
            data["scope"] = self.scope
        return data


OAUTH_CLASSES_MAP = {
    "client_secret_basic": ClientSecretBasic,
    "client_secret_post": ClientSecretPost,
    "client_secret_jwt": ClientSecretJwt,
    "private_key_jwt": PrivateKeyJwt,
}


def create_oauth_provider(args: dict[str, Any]) -> OAuth2TokenProvider:
    """
    This factory method creates an instance of  OAuth2TokenProvider
    """
    required_keys = [
        "sasl_oauth_token_endpoint",
        "sasl_oauth_client_id",
    ]
    for key in required_keys:
        if key not in args:
            msg = "OAUTHBEARER requires these mandatory " f"setting {required_keys}"
            raise ValueError(msg)

    sasl_oauth_method = args.get("sasl_oauth_method", "client_secret_basic")

    if sasl_oauth_method not in OAUTH_CLASSES_MAP:
        msg = (
            f"OAUTHBEARER invalid sasl_oauth_method: {sasl_oauth_method}. "
            f"Should be one of : {','.join(OAUTH_CLASSES_MAP)}"
        )
        raise ValueError(msg)

    if sasl_oauth_method in PRIVATE_KEY_METHODS and not args.get(
        "sasl_oauth_private_keyfile"
    ):
        msg = (
            f"When using {sasl_oauth_method} a private key file is needed. "
            "Please provide sasl_oauth_private_keyfile"
        )
        raise ValueError(msg)

    if sasl_oauth_method in CLIENT_SECRET_METHODS and not args.get(
        "sasl_oauth_client_secret"
    ):
        msg = (
            f"When using {sasl_oauth_method} a client secret is needed. "
            "Please provide sasl_oauth_client_secret"
        )
        raise ValueError(msg)

    return OAUTH_CLASSES_MAP[sasl_oauth_method](**args)
