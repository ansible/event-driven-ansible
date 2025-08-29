# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

from http.client import HTTPMessage
from typing import Any, Iterator, Literal, Optional, Union

from typing_extensions import LiteralString

__metaclass__ = type

import json
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import pytest
from ansible_collections.ansible.eda.plugins.module_utils.client import (  # type: ignore
    Client,
)
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    AuthError,
    EDAHTTPError,
)

ENDPOINT = "/api/test_endpoint"
QUERY_PARAMS = {"param": "value"}
ID = 1
DATA = {"key": "value"}
JSON_DATA = '{"key": "value"}'


@pytest.fixture
def mock_response() -> Mock:
    response = Mock()
    response.status = 200
    response.read.return_value = JSON_DATA.encode("utf-8")
    response.headers = {"content-type": "application/json"}
    return response


@pytest.fixture
def mock_error_response() -> Mock:
    response = Mock()
    response.status = 401
    response.read.return_value = b"Unauthorized"
    response.headers = {}
    return response


@pytest.fixture
def mock_http_error() -> HTTPError:
    return HTTPError(
        url="http://example.com",
        code=401,
        msg="Unauthorized",
        hdrs=HTTPMessage(),
        fp=None,
    )


@pytest.fixture
def mock_url_error() -> URLError:
    return URLError("URL error")


@pytest.fixture
def client() -> Iterator[tuple[Client, Mock]]:
    with patch(
        "ansible_collections.ansible.eda.plugins.module_utils.client.Request"
    ) as mock_request:
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance
        client_instance = Client(
            host="http://mocked-url.com",
            username="mocked_user",
            password="mocked_pass",
            timeout=10,
            validate_certs=True,
        )
        yield client_instance, mock_request_instance


@pytest.fixture
def token_client() -> Iterator[tuple[Client, Mock]]:
    with patch(
        "ansible_collections.ansible.eda.plugins.module_utils.client.Request"
    ) as mock_request:
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance
        client_instance = Client(
            host="http://mocked-url.com",
            token="test_token_123",
            timeout=10,
            validate_certs=True,
        )
        yield client_instance, mock_request_instance


@pytest.mark.parametrize(
    "input_host, expected_host",
    [
        ("example.com", "https://example.com"),
        ("mocked-url.com", "https://mocked-url.com"),
        ("http://example.com", "http://example.com"),
        ("https://example.com", "https://example.com"),
        ("example.com:8080", "https://example.com:8080"),
        ("http://example.com:8000", "http://example.com:8000"),
        ("https://example.com:8443", "https://example.com:8443"),
    ],
)
def test_client_init_host_processing_valid_inputs(
    input_host: str, expected_host: str
) -> None:
    """
    Tests the host processing logic in the Client's __init__ method for valid, non-empty inputs.
    """
    client_instance = Client(host=input_host)
    assert client_instance.host == expected_host


@pytest.mark.parametrize(
    "invalid_host_input",
    [
        None,
        "",
    ],
)
def test_client_init_invalid_host_raises_error(
    invalid_host_input: Optional[str],
) -> None:
    """
    Tests that passing host=None or host="" raises a ValueError.
    """
    with pytest.raises(ValueError, match="Host must be a non-empty string."):
        Client(host=invalid_host_input)


def test_client_init_attributes_assignment() -> None:
    """
    Tests that other attributes are correctly assigned during __init__,
    along with host processing.
    """
    client_instance = Client(
        host="example",
        username="testuser",
        password="testpass",
        timeout=42,
        validate_certs=False,
    )
    assert client_instance.host == "https://example"
    assert client_instance.username == "testuser"
    assert client_instance.password == "testpass"
    assert client_instance.timeout == 42
    assert client_instance.validate_certs is False


def test_client_init_default_optional_attributes() -> None:
    """
    Tests that optional attributes are None by default when not provided.
    """
    client_instance = Client(host="example.com")
    assert client_instance.host == "https://example.com"
    assert client_instance.username is None
    assert client_instance.password is None
    assert client_instance.timeout is None
    assert client_instance.validate_certs is None


@pytest.mark.parametrize(
    "method, status_code, expected_response, exception_type, exception_message, headers, data",
    [
        ("get", 200, DATA, None, None, {}, None),
        ("post", 201, DATA, None, None, {"Content-Type": "application/json"}, DATA),
        ("patch", 200, DATA, None, None, {"Content-Type": "application/json"}, DATA),
        ("delete", 204, {}, None, None, {}, None),
        (
            "post",
            401,
            None,
            AuthError,
            "Failed to authenticate with the instance: 401 Unauthorized",
            {"Content-Type": "application/json"},
            DATA,
        ),
        ("get", 404, DATA, None, None, {}, None),
        ("get", None, None, EDAHTTPError, "URL error", {}, None),
    ],
)
def test_client_methods(
    method: str,
    status_code: Optional[
        Union[Literal[200], Literal[201], Literal[204], Literal[401], Literal[404]]
    ],
    expected_response: Optional[dict[str, str]],
    exception_type: Optional[Any],
    exception_message: Optional[Union[LiteralString, Literal["URL error"]]],
    headers: dict[str, str],
    data: Optional[dict[str, str]],
    client: tuple[Any, Mock],
    mock_response: Mock,
    mock_http_error: HTTPError,
    mock_url_error: URLError,
) -> None:
    client_instance, mock_request_instance = client
    mock_request_instance.open = Mock()

    if exception_type:
        if exception_type == AuthError:
            mock_request_instance.open.side_effect = mock_http_error
            with pytest.raises(exception_type, match=exception_message):
                getattr(client_instance, method)(ENDPOINT, data=data, headers=headers)
        elif exception_type == EDAHTTPError:
            mock_request_instance.open.side_effect = mock_url_error
            with pytest.raises(exception_type, match=exception_message):
                getattr(client_instance, method)(ENDPOINT, data=data, headers=headers)
    else:
        mock_response.status = status_code
        mock_response.read.return_value = json.dumps(expected_response).encode("utf-8")
        mock_request_instance.open.return_value = mock_response

        response = getattr(client_instance, method)(
            ENDPOINT, data=data, headers=headers
        )
        assert response.status == status_code
        assert response.json == expected_response


def test_client_init_with_token() -> None:
    """
    Tests that Client initializes correctly with token authentication.
    """
    client_instance = Client(host="example.com", token="test_token_123")
    assert client_instance.host == "https://example.com"
    assert client_instance.username is None
    assert client_instance.password is None
    assert client_instance.token == "test_token_123"
    assert client_instance.timeout is None
    assert client_instance.validate_certs is None


def test_client_init_token_with_credentials() -> None:
    """
    Tests that Client initializes correctly when both token and username/password are provided.
    Token should take precedence in authentication logic.
    """
    client_instance = Client(
        host="example.com",
        username="testuser",
        password="testpass",
        token="test_token_123",
    )
    assert client_instance.host == "https://example.com"
    assert client_instance.username == "testuser"
    assert client_instance.password == "testpass"
    assert client_instance.token == "test_token_123"


@pytest.mark.parametrize(
    "method, expected_auth_header, expected_status",
    [
        ("get", "Bearer test_token_123", 200),
        ("post", "Bearer test_token_123", 201),
        ("patch", "Bearer test_token_123", 200),
        ("delete", "Bearer test_token_123", 204),
    ],
)
def test_client_token_auth_sets_bearer_header(
    method: str,
    expected_auth_header: str,
    expected_status: int,
    token_client: tuple[Client, Mock],
    mock_response: Mock,
) -> None:
    """
    Tests that token authentication correctly sets the Authorization: Bearer header.
    """
    client_instance, mock_request_instance = token_client
    mock_request_instance.open = Mock()
    mock_response.status = expected_status
    mock_response.read.return_value = json.dumps(DATA).encode("utf-8")
    mock_request_instance.open.return_value = mock_response

    # Call the method
    getattr(client_instance, method)(
        ENDPOINT, data=DATA if method in ["post", "patch"] else None
    )

    # Verify the request was called with Bearer authorization header
    mock_request_instance.open.assert_called_once()
    call_args = mock_request_instance.open.call_args
    headers = call_args.kwargs.get("headers", {})
    assert "Authorization" in headers
    assert headers["Authorization"] == expected_auth_header


def test_client_token_auth_skips_basic_auth(
    token_client: tuple[Client, Mock],
    mock_response: Mock,
) -> None:
    """
    Tests that when token is present, username/password are not used for basic auth.
    """
    client_instance, mock_request_instance = token_client
    # Set username/password on the client to verify they're ignored
    client_instance.username = "should_be_ignored"
    client_instance.password = "should_be_ignored"

    mock_request_instance.open = Mock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(DATA).encode("utf-8")
    mock_request_instance.open.return_value = mock_response

    # Make a GET request
    client_instance.get(ENDPOINT)

    # Verify the request was called without username/password auth
    mock_request_instance.open.assert_called_once()
    call_args = mock_request_instance.open.call_args
    assert call_args.kwargs.get("url_username") is None
    assert call_args.kwargs.get("url_password") is None

    # But should have Bearer token in headers
    headers = call_args.kwargs.get("headers", {})
    assert headers.get("Authorization") == "Bearer test_token_123"


def test_client_basic_auth_when_no_token(
    client: tuple[Client, Mock],
    mock_response: Mock,
) -> None:
    """
    Tests that username/password authentication is used when no token is present.
    """
    client_instance, mock_request_instance = client
    mock_request_instance.open = Mock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(DATA).encode("utf-8")
    mock_request_instance.open.return_value = mock_response

    # Make a GET request
    client_instance.get(ENDPOINT)

    # Verify the request was called with username/password auth
    mock_request_instance.open.assert_called_once()
    call_args = mock_request_instance.open.call_args
    assert call_args.kwargs.get("url_username") == "mocked_user"
    assert call_args.kwargs.get("url_password") == "mocked_pass"

    # Should not have Authorization header for basic auth (handled by Request)
    headers = call_args.kwargs.get("headers", {})
    assert "Authorization" not in headers


@pytest.mark.parametrize(
    "method, data_present, expected_status",
    [
        ("get", False, 200),
        ("post", True, 201),
        ("patch", True, 200),
        ("delete", False, 204),
    ],
)
def test_client_token_auth_preserves_existing_headers(
    method: str,
    data_present: bool,
    expected_status: int,
    token_client: tuple[Client, Mock],
    mock_response: Mock,
) -> None:
    """
    Tests that token authentication preserves existing headers while adding Authorization.
    """
    client_instance, mock_request_instance = token_client
    mock_request_instance.open = Mock()
    mock_response.status = expected_status
    mock_response.read.return_value = json.dumps(DATA).encode("utf-8")
    mock_request_instance.open.return_value = mock_response

    # Custom headers to test preservation
    custom_headers = {"X-Custom-Header": "custom_value"}
    kwargs = {"headers": custom_headers}
    if data_present:
        kwargs["data"] = DATA

    # Call the method with custom headers
    getattr(client_instance, method)(ENDPOINT, **kwargs)

    # Verify the request includes both custom and auth headers
    mock_request_instance.open.assert_called_once()
    call_args = mock_request_instance.open.call_args
    headers = call_args.kwargs.get("headers", {})

    # Should have both custom header and Authorization
    assert headers["X-Custom-Header"] == "custom_value"
    assert headers["Authorization"] == "Bearer test_token_123"

    # POST/PATCH should also have Content-Type
    if data_present:
        assert headers["Content-Type"] == "application/json"
