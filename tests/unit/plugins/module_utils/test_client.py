# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

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
def mock_response():
    response = Mock()
    response.status = 200
    response.read.return_value = JSON_DATA.encode("utf-8")
    response.headers = {"content-type": "application/json"}
    return response


@pytest.fixture
def mock_error_response():
    response = Mock()
    response.status = 401
    response.read.return_value = b"Unauthorized"
    response.headers = {}
    return response


@pytest.fixture
def mock_http_error():
    return HTTPError(
        url="http://example.com", code=401, msg="Unauthorized", hdrs={}, fp=None
    )


@pytest.fixture
def mock_url_error():
    return URLError("URL error")


@pytest.fixture
def client():
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
    method,
    status_code,
    expected_response,
    exception_type,
    exception_message,
    headers,
    data,
    client,
    mock_response,
    mock_http_error,
    mock_url_error,
):
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
