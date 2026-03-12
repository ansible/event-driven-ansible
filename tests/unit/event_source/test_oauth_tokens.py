import tempfile
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import jwt
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import CertificateBuilder, Name, NameAttribute, NameOID

from extensions.eda.plugins.event_source.oauth_tokens import (
    CLIENT_SECRET_METHODS,
    DEFAULT_ALGORITHM,
    DEFAULT_JWT_DURATION,
    GRANT_TYPE,
    JWT_BEARER_ASSERTION_TYPE,
    OAUTH_CLASSES_MAP,
    PRIVATE_KEY_METHODS,
    VALID_OAUTH_METHODS,
    ClientSecretBasic,
    ClientSecretJwt,
    ClientSecretPost,
    OAuth2TokenProvider,
    PrivateKeyJwt,
    create_oauth_provider,
)


class ConcreteOAuth2TokenProvider(OAuth2TokenProvider):
    def _create_payload(self) -> Dict[str, Any]:
        return {"grant_type": "client_credentials"}


class TestOAuth2TokenProvider:
    def test_init_with_required_params(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)

        assert provider.token_endpoint == "https://auth.example.com/token"
        assert provider.client_id == "test-client"
        assert provider.client_secret is None
        assert provider.scope is None
        assert provider.algorithm == DEFAULT_ALGORITHM
        assert provider.token_duration_in_minutes == int(DEFAULT_JWT_DURATION)
        assert provider.subject == "test-client"
        assert provider.issuer == "test-client"
        assert provider.audience == "https://auth.example.com/token"
        assert provider.access_token is None
        assert provider.token_expires_at == 0
        assert provider.auth is None

    def test_init_with_optional_params(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "secret",
            "sasl_oauth_scope": "read write",
            "sasl_oauth_algorithm": "HS256",
            "sasl_oauth_token_duration": "60",
            "sasl_oauth_subject": "custom-subject",
            "sasl_oauth_issuer": "custom-issuer",
            "sasl_oauth_audience": "custom-audience",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)

        assert provider.client_secret == "secret"
        assert provider.scope == "read write"
        assert provider.algorithm == "HS256"
        assert provider.token_duration_in_minutes == 60
        assert provider.subject == "custom-subject"
        assert provider.issuer == "custom-issuer"
        assert provider.audience == "custom-audience"

    @pytest.mark.asyncio
    async def test_token_returns_cached_token_when_valid(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider.access_token = "cached-token"  # type: ignore[assignment]
        provider.token_expires_at = int(time.time() + 600)  # 10 minutes in future

        result = await provider.token()
        assert result == "cached-token"

    @pytest.mark.asyncio
    async def test_token_requests_new_token_when_expired(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider.access_token = "expired-token"  # type: ignore[assignment]
        provider.token_expires_at = int(time.time() - 100)  # Already expired

        with patch.object(
            provider, "_request_new_token", return_value="new-token"
        ) as mock_request:
            result = await provider.token()
            assert result == "new-token"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_requests_new_token_when_near_expiry(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider.access_token = "soon-expired-token"  # type: ignore[assignment]
        provider.token_expires_at = int(time.time() + 200)  # Less than 5 min buffer

        with patch.object(
            provider, "_request_new_token", return_value="new-token"
        ) as mock_request:
            result = await provider.token()
            assert result == "new-token"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_new_token_success(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider._create_payload = MagicMock(  # type: ignore[method-assign]
            return_value={"grant_type": "client_credentials"}
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(
            return_value={"access_token": "new-access-token", "expires_in": 3600}
        )

        # Mock session and its context managers
        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock the ClientSession context manager
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            result = await provider._request_new_token()

            assert result == "new-access-token"
            assert provider.access_token == "new-access-token"
            assert provider.token_expires_at > time.time()

    @pytest.mark.asyncio
    async def test_request_new_token_http_error(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider._create_payload = MagicMock(  # type: ignore[method-assign]
            return_value={"grant_type": "client_credentials"}
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=401
        )

        # Mock session and its context managers
        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock the ClientSession context manager
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            with pytest.raises(aiohttp.ClientResponseError):
                await provider._request_new_token()

    @pytest.mark.asyncio
    async def test_request_new_token_missing_access_token(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)
        provider._create_payload = MagicMock(  # type: ignore[method-assign]
            return_value={"grant_type": "client_credentials"}
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(
            return_value={"expires_in": 3600}
        )  # Missing access_token

        # Mock session and its context managers
        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock the ClientSession context manager
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
            with pytest.raises(KeyError):
                await provider._request_new_token()

    def test_create_jwt_payload(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_subject": "test-subject",
            "sasl_oauth_issuer": "test-issuer",
            "sasl_oauth_audience": "test-audience",
            "sasl_oauth_token_duration": "45",
        }
        provider = ConcreteOAuth2TokenProvider(**kwargs)

        payload = provider._create_jwt_payload()

        assert payload["sub"] == "test-subject"
        assert payload["iss"] == "test-issuer"
        assert payload["aud"] == "test-audience"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        assert isinstance(payload["jti"], str)

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }

        with pytest.raises(TypeError):
            OAuth2TokenProvider(**kwargs)


class TestClientSecretBasic:
    def test_init(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }
        provider = ClientSecretBasic(**kwargs)

        assert provider.auth.login == "test-client"  # type: ignore[union-attr]
        assert provider.auth.password == "test-secret"  # type: ignore[union-attr]

    def test_create_payload_without_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }
        provider = ClientSecretBasic(**kwargs)

        payload = provider._create_payload()

        expected = {"grant_type": GRANT_TYPE}
        assert payload == expected

    def test_create_payload_with_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_scope": "read write",
        }
        provider = ClientSecretBasic(**kwargs)

        payload = provider._create_payload()

        expected = {"grant_type": GRANT_TYPE, "scope": "read write"}
        assert payload == expected


class TestClientSecretPost:
    def test_create_payload_without_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }
        provider = ClientSecretPost(**kwargs)

        payload = provider._create_payload()

        expected = {
            "grant_type": GRANT_TYPE,
            "client_id": "test-client",
            "client_secret": "test-secret",
        }
        assert payload == expected

    def test_create_payload_with_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_scope": "read write",
        }
        provider = ClientSecretPost(**kwargs)

        payload = provider._create_payload()

        expected = {
            "grant_type": GRANT_TYPE,
            "client_id": "test-client",
            "client_secret": "test-secret",
            "scope": "read write",
        }
        assert payload == expected


class TestClientSecretJwt:
    def test_create_payload_without_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }
        provider = ClientSecretJwt(**kwargs)

        payload = provider._create_payload()

        expected_keys = {
            "grant_type": "client_credentials",
            "client_id": "test-client",
            "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
        }

        # Check that all expected keys are present
        for key, value in expected_keys.items():
            assert payload[key] == value

        # Check that client_assertion is present and is a valid JWT string
        assert "client_assertion" in payload
        client_assertion = payload["client_assertion"]
        assert isinstance(client_assertion, str)
        assert (
            len(client_assertion.split(".")) == 3
        )  # JWT has 3 parts separated by dots

        # Decode the JWT to verify it was created correctly
        decoded = jwt.decode(
            client_assertion,
            "test-secret",
            algorithms=["HS256"],
            audience="https://auth.example.com/token",
        )
        assert decoded["sub"] == "test-client"
        assert decoded["iss"] == "test-client"
        assert decoded["aud"] == "https://auth.example.com/token"

    def test_create_payload_with_scope(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_scope": "read write",
        }
        provider = ClientSecretJwt(**kwargs)

        payload = provider._create_payload()

        expected_keys = {
            "grant_type": "client_credentials",
            "client_id": "test-client",
            "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
            "scope": "read write",
        }

        # Check that all expected keys are present
        for key, value in expected_keys.items():
            assert payload[key] == value

        # Check that client_assertion is present and is a valid JWT string
        assert "client_assertion" in payload
        client_assertion = payload["client_assertion"]
        assert isinstance(client_assertion, str)
        assert (
            len(client_assertion.split(".")) == 3
        )  # JWT has 3 parts separated by dots


class TestPrivateKeyJwt:
    def test_init(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_public_keyfile": "/path/to/public.pem",
        }
        provider = PrivateKeyJwt(**kwargs)

        assert provider.private_keyfile == "/path/to/private.key"
        assert provider.public_keyfile == "/path/to/public.pem"

    def test_init_without_public_key(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
        }
        provider = PrivateKeyJwt(**kwargs)

        assert provider.private_keyfile == "/path/to/private.key"
        assert provider.public_keyfile is None

    def test_get_public_cert_thumbprint(self) -> None:
        # Create a test certificate
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = Name(
            [
                NameAttribute(NameOID.COMMON_NAME, "test"),
            ]
        )

        cert = (
            CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(1)
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(private_key, hashes.SHA256())
        )

        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as temp_file:
            temp_file.write(cert_pem)
            temp_file_path = temp_file.name

        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_public_keyfile": temp_file_path,
        }
        provider = PrivateKeyJwt(**kwargs)

        try:
            x5t_value, x5t_s256_value = provider._get_public_cert_thumbprint()

            assert isinstance(x5t_value, str)
            assert isinstance(x5t_s256_value, str)
            assert len(x5t_value) > 0
            assert len(x5t_s256_value) > 0
        finally:
            import os

            os.unlink(temp_file_path)

    @patch("uuid.uuid4")
    def test_create_jwt_headers_without_public_key(self, mock_uuid: Mock) -> None:
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-9012-123456789012")

        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_algorithm": "RS256",
        }
        provider = PrivateKeyJwt(**kwargs)

        headers = provider._create_jwt_headers()

        expected = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": "12345678-1234-5678-9012-123456789012",
        }
        assert headers == expected

    @patch("uuid.uuid4")
    def test_create_jwt_headers_with_public_key(self, mock_uuid: Mock) -> None:
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-9012-123456789012")

        # Create a test certificate
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = Name(
            [
                NameAttribute(NameOID.COMMON_NAME, "test"),
            ]
        )

        cert = (
            CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(1)
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(private_key, hashes.SHA256())
        )

        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as temp_file:
            temp_file.write(cert_pem)
            public_key_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": "/path/to/private.key",
                "sasl_oauth_public_keyfile": public_key_path,
                "sasl_oauth_algorithm": "RS256",
            }
            provider = PrivateKeyJwt(**kwargs)

            headers = provider._create_jwt_headers()

            # Verify the basic structure
            assert headers["alg"] == "RS256"
            assert headers["typ"] == "JWT"
            assert headers["kid"] == "12345678-1234-5678-9012-123456789012"

            # Verify x5t and x5t#S256 thumbprints are present and are valid
            # base64url strings
            assert "x5t" in headers
            assert "x5t#S256" in headers
            assert isinstance(headers["x5t"], str)
            assert isinstance(headers["x5t#S256"], str)
            assert len(headers["x5t"]) > 0
            assert len(headers["x5t#S256"]) > 0

            # Test that thumbprints are valid base64url
            # (no padding, URL-safe characters)
            import base64

            # Should not raise an exception when decoding
            # Add padding for decoding
            base64.urlsafe_b64decode(headers["x5t"] + "===")
            base64.urlsafe_b64decode(
                headers["x5t#S256"] + "==="
            )  # Add padding for decoding

        finally:
            import os

            os.unlink(public_key_path)

    def test_create_payload_without_scope(self) -> None:
        # Generate a test RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".key", delete=False
        ) as temp_file:
            temp_file.write(private_key_pem)
            private_key_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": private_key_path,
            }
            provider = PrivateKeyJwt(**kwargs)

            payload = provider._create_payload()

            expected_keys = {
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
            }

            # Check that all expected keys are present
            for key, value in expected_keys.items():
                assert payload[key] == value

            # Check that client_assertion is present and is a valid JWT string
            assert "client_assertion" in payload
            client_assertion = payload["client_assertion"]
            assert isinstance(client_assertion, str)
            assert (
                len(client_assertion.split(".")) == 3
            )  # JWT has 3 parts separated by dots

            # Verify the JWT can be decoded with the public key
            public_key = private_key.public_key()
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            decoded = jwt.decode(
                client_assertion,
                public_key_pem,
                algorithms=["RS256"],
                audience="https://auth.example.com/token",
            )
            assert decoded["sub"] == "test-client"
            assert decoded["iss"] == "test-client"
            assert decoded["aud"] == "https://auth.example.com/token"

        finally:
            import os

            os.unlink(private_key_path)

    def test_create_payload_with_scope(self) -> None:
        # Generate a test RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".key", delete=False
        ) as temp_file:
            temp_file.write(private_key_pem)
            private_key_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": private_key_path,
                "sasl_oauth_scope": "read write",
            }
            provider = PrivateKeyJwt(**kwargs)

            payload = provider._create_payload()

            expected_keys = {
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_assertion_type": JWT_BEARER_ASSERTION_TYPE,
                "scope": "read write",
            }

            # Check that all expected keys are present
            for key, value in expected_keys.items():
                assert payload[key] == value

            # Check that client_assertion is present and is a valid JWT string
            assert "client_assertion" in payload
            client_assertion = payload["client_assertion"]
            assert isinstance(client_assertion, str)
            assert (
                len(client_assertion.split(".")) == 3
            )  # JWT has 3 parts separated by dots

        finally:
            import os

            os.unlink(private_key_path)

    def test_create_payload_with_bad_private_key_file(self) -> None:
        # Create a file with invalid private key content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".key", delete=False
        ) as temp_file:
            temp_file.write("This is not a valid private key")
            bad_key_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": bad_key_path,
            }
            provider = PrivateKeyJwt(**kwargs)

            # Should raise an error when trying to create JWT with bad key
            with pytest.raises((ValueError, TypeError, jwt.InvalidKeyError)):
                provider._create_payload()

        finally:
            import os

            os.unlink(bad_key_path)

    def test_create_payload_with_nonexistent_private_key_file(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/nonexistent/path/to/private.key",
        }
        provider = PrivateKeyJwt(**kwargs)

        # Should raise FileNotFoundError when trying to read nonexistent file
        with pytest.raises(FileNotFoundError):
            provider._create_payload()

    def test_get_public_cert_thumbprint_with_bad_certificate_file(self) -> None:
        # Create a file with invalid certificate content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as temp_file:
            temp_file.write("This is not a valid certificate")
            bad_cert_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": "/path/to/private.key",
                "sasl_oauth_public_keyfile": bad_cert_path,
            }
            provider = PrivateKeyJwt(**kwargs)

            # Should raise an error when trying to parse bad certificate
            with pytest.raises((ValueError, TypeError)):
                provider._get_public_cert_thumbprint()

        finally:
            import os

            os.unlink(bad_cert_path)

    def test_get_public_cert_thumbprint_with_nonexistent_certificate_file(self) -> None:
        kwargs = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_public_keyfile": "/nonexistent/path/to/public.pem",
        }
        provider = PrivateKeyJwt(**kwargs)

        # Should raise FileNotFoundError when trying to read nonexistent file
        with pytest.raises(FileNotFoundError):
            provider._get_public_cert_thumbprint()

    def test_create_jwt_headers_with_bad_certificate_file(self) -> None:
        # Create a file with invalid certificate content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as temp_file:
            temp_file.write(
                (
                    "-----BEGIN CERTIFICATE-----\n"
                    "Invalid certificate content\n"
                    "-----END CERTIFICATE-----"
                )
            )
            bad_cert_path = temp_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": "/path/to/private.key",
                "sasl_oauth_public_keyfile": bad_cert_path,
                "sasl_oauth_algorithm": "RS256",
            }
            provider = PrivateKeyJwt(**kwargs)

            # Should raise an error when trying to create headers with bad certificate
            with pytest.raises((ValueError, TypeError)):
                provider._create_jwt_headers()

        finally:
            import os

            os.unlink(bad_cert_path)

    def test_create_payload_with_mismatched_key_and_cert(self) -> None:
        # Create two different key pairs
        private_key1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Create private key file with key1
        private_key1_pem = private_key1.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        # Create certificate with key2 (mismatched)
        subject = issuer = Name([NameAttribute(NameOID.COMMON_NAME, "test")])
        cert = (
            CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key2.public_key())
            .serial_number(1)
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(private_key2, hashes.SHA256())
        )

        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".key", delete=False
        ) as key_file:
            key_file.write(private_key1_pem)
            key_path = key_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as cert_file:
            cert_file.write(cert_pem)
            cert_path = cert_file.name

        try:
            kwargs = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_private_keyfile": key_path,
                "sasl_oauth_public_keyfile": cert_path,
            }
            provider = PrivateKeyJwt(**kwargs)

            # This should still work for creating the payload
            # (mismatched key/cert is often allowed)
            # but the certificate thumbprint should be calculated correctly
            payload = provider._create_payload()
            assert "client_assertion" in payload

            # The thumbprint calculation should work (it only reads
            # the cert, not the key)
            x5t_value, x5t_s256_value = provider._get_public_cert_thumbprint()
            assert isinstance(x5t_value, str)
            assert isinstance(x5t_s256_value, str)

        finally:
            import os

            os.unlink(key_path)
            os.unlink(cert_path)


class TestCreateOAuthProvider:
    def test_create_client_secret_basic_default(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }

        provider = create_oauth_provider(args)

        assert isinstance(provider, ClientSecretBasic)

    def test_create_client_secret_basic_explicit(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_method": "client_secret_basic",
        }

        provider = create_oauth_provider(args)

        assert isinstance(provider, ClientSecretBasic)

    def test_create_client_secret_jwt(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_method": "client_secret_jwt",
        }

        provider = create_oauth_provider(args)

        assert isinstance(provider, ClientSecretJwt)

    def test_create_private_key_jwt(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_method": "private_key_jwt",
        }

        provider = create_oauth_provider(args)

        assert isinstance(provider, PrivateKeyJwt)

    def test_missing_token_endpoint(self) -> None:
        args = {
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
        }

        with pytest.raises(ValueError, match="OAUTHBEARER requires these mandatory"):
            create_oauth_provider(args)

    def test_missing_client_id(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_secret": "test-secret",
        }

        with pytest.raises(ValueError, match="OAUTHBEARER requires these mandatory"):
            create_oauth_provider(args)

    def test_invalid_oauth_method(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_method": "invalid_method",
        }

        with pytest.raises(
            ValueError,
            match=(
                "OAUTHBEARER invalid sasl_oauth_method: "
                "invalid_method. Should be one of"
            ),
        ):
            create_oauth_provider(args)

    def test_missing_client_secret_for_client_secret_method(self) -> None:
        # Test default method (client_secret_basic) without client_secret
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }

        with pytest.raises(
            ValueError,
            match=(
                "When using client_secret_basic a client secret is "
                "needed. Please provide sasl_oauth_client_secret"
            ),
        ):
            create_oauth_provider(args)

    def test_missing_private_key_for_private_key_method(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_method": "private_key_jwt",
        }

        with pytest.raises(
            ValueError,
            match=(
                "When using private_key_jwt a private key file is "
                "needed. Please provide sasl_oauth_private_keyfile"
            ),
        ):
            create_oauth_provider(args)

    def test_missing_client_secret_for_explicit_client_secret_method(self) -> None:
        for method in CLIENT_SECRET_METHODS:
            args = {
                "sasl_oauth_token_endpoint": "https://auth.example.com/token",
                "sasl_oauth_client_id": "test-client",
                "sasl_oauth_method": method,
            }

            with pytest.raises(
                ValueError,
                match=(
                    f"When using {method} a client secret is needed. "
                    "Please provide sasl_oauth_client_secret"
                ),
            ):
                create_oauth_provider(args)

    def test_create_client_secret_post(self) -> None:
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_method": "client_secret_post",
        }

        provider = create_oauth_provider(args)

        assert isinstance(provider, ClientSecretPost)

    def test_constants_structure(self) -> None:
        # Test CLIENT_SECRET_METHODS constant
        expected_client_secret_methods = [
            "client_secret_basic",
            "client_secret_post",
            "client_secret_jwt",
        ]
        assert CLIENT_SECRET_METHODS == expected_client_secret_methods

        # Test PRIVATE_KEY_METHODS constant
        expected_private_key_methods = [
            "private_key_jwt",
        ]
        assert PRIVATE_KEY_METHODS == expected_private_key_methods

        # Test VALID_OAUTH_METHODS is combination of both
        assert VALID_OAUTH_METHODS == CLIENT_SECRET_METHODS + PRIVATE_KEY_METHODS

    def test_oauth_classes_map(self) -> None:
        # Test that OAUTH_CLASSES_MAP has correct mappings
        expected_mapping = {
            "client_secret_basic": ClientSecretBasic,
            "client_secret_post": ClientSecretPost,
            "client_secret_jwt": ClientSecretJwt,
            "private_key_jwt": PrivateKeyJwt,
        }
        assert OAUTH_CLASSES_MAP == expected_mapping

    def test_all_valid_oauth_methods_work(self) -> None:
        base_args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
        }

        # Test client_secret methods
        for method in CLIENT_SECRET_METHODS:
            args = {
                **base_args,
                "sasl_oauth_client_secret": "test-secret",
                "sasl_oauth_method": method,
            }
            provider = create_oauth_provider(args)
            expected_class = OAUTH_CLASSES_MAP[method]
            assert isinstance(provider, expected_class)

        # Test private_key_jwt method
        args = {
            **base_args,
            "sasl_oauth_private_keyfile": "/path/to/private.key",
            "sasl_oauth_method": "private_key_jwt",
        }
        provider = create_oauth_provider(args)
        assert isinstance(provider, PrivateKeyJwt)

    def test_method_validation_order(self) -> None:
        # Test that method validation happens before credential validation
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_method": "invalid_method",
            # No credentials provided, but method validation should fail first
        }

        with pytest.raises(
            ValueError, match="OAUTHBEARER invalid sasl_oauth_method: invalid_method"
        ):
            create_oauth_provider(args)

    def test_factory_uses_class_map(self) -> None:
        # Test that factory properly uses OAUTH_CLASSES_MAP
        args = {
            "sasl_oauth_token_endpoint": "https://auth.example.com/token",
            "sasl_oauth_client_id": "test-client",
            "sasl_oauth_client_secret": "test-secret",
            "sasl_oauth_method": "client_secret_basic",
        }

        provider = create_oauth_provider(args)

        # Should create the class from the map
        expected_class = OAUTH_CLASSES_MAP["client_secret_basic"]
        assert isinstance(provider, expected_class)
        assert isinstance(provider, ClientSecretBasic)
