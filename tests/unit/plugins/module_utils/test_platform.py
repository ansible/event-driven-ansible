# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.eda.plugins.module_utils.client import (  # type: ignore
    Client,
)
from ansible_collections.ansible.eda.plugins.module_utils.controller import (  # type: ignore
    Controller,
)


def create_mock_module(params: Optional[Dict[str, Any]] = None) -> Mock:
    """Create a mock AnsibleModule with the given parameters."""
    mock_module = Mock(spec=AnsibleModule)
    mock_module.params = params or {}
    return mock_module


@pytest.fixture
def token_module_params() -> Dict[str, Any]:
    """Module parameters for token authentication."""
    return {
        "controller_host": "https://aap.example.com",
        "controller_token": "test_token_123",
        "request_timeout": 30.0,
        "validate_certs": True,
    }


@pytest.fixture
def basic_auth_module_params() -> Dict[str, Any]:
    """Module parameters for username/password authentication."""
    return {
        "controller_host": "https://aap.example.com",
        "controller_username": "testuser",
        "controller_password": "testpass",
        "request_timeout": 30.0,
        "validate_certs": True,
    }


@pytest.fixture
def mixed_auth_module_params() -> Dict[str, Any]:
    """Module parameters with both token and username/password."""
    return {
        "controller_host": "https://aap.example.com",
        "controller_token": "test_token_123",
        "controller_username": "testuser",
        "controller_password": "testpass",
        "request_timeout": 30.0,
        "validate_certs": True,
    }


class TestControllerTokenValidation:
    """Test controller_token validation scenarios."""

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_client_creation_with_controller_token(
        self, mock_request: Mock, token_module_params: Dict[str, Any]
    ) -> None:
        """Test Client creation using controller_token parameter."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        # Create client as modules would
        client = Client(
            host=token_module_params.get("controller_host"),
            username=token_module_params.get("controller_username"),
            password=token_module_params.get("controller_password"),
            token=token_module_params.get("controller_token"),
            timeout=token_module_params.get("request_timeout"),
            validate_certs=token_module_params.get("validate_certs"),
        )

        assert client.host == "https://aap.example.com"
        assert client.token == "test_token_123"
        assert client.username is None
        assert client.password is None

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_precedence_over_basic_auth(
        self, mock_request: Mock, mixed_auth_module_params: Dict[str, Any]
    ) -> None:
        """Test that controller_token takes precedence over username/password."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        client = Client(
            host=mixed_auth_module_params.get("controller_host"),
            username=mixed_auth_module_params.get("controller_username"),
            password=mixed_auth_module_params.get("controller_password"),
            token=mixed_auth_module_params.get("controller_token"),
            timeout=mixed_auth_module_params.get("request_timeout"),
            validate_certs=mixed_auth_module_params.get("validate_certs"),
        )

        # Both should be stored, but token should take precedence in usage
        assert client.token == "test_token_123"
        assert client.username == "testuser"
        assert client.password == "testpass"

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_authentication_flow(
        self, mock_request: Mock, token_module_params: Dict[str, Any]
    ) -> None:
        """Test the complete authentication flow using controller_token."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"result": "success"}'
        mock_response.headers = {"content-type": "application/json"}
        mock_request_instance.open.return_value = mock_response

        client = Client(
            host=token_module_params.get("controller_host"),
            token=token_module_params.get("controller_token"),
            timeout=token_module_params.get("request_timeout"),
            validate_certs=token_module_params.get("validate_certs"),
        )

        # Make a request
        response = client.get("/test-endpoint")

        # Verify request was made with correct token authentication
        mock_request_instance.open.assert_called_once()
        call_args = mock_request_instance.open.call_args

        # Check that url_username and url_password are None (not using basic auth)
        assert call_args.kwargs.get("url_username") is None
        assert call_args.kwargs.get("url_password") is None

        # Check that Authorization header was set correctly
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer test_token_123"

        assert response.status == 200
        assert response.json == {"result": "success"}

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_with_controller_instance(
        self, mock_request: Mock, token_module_params: Dict[str, Any]
    ) -> None:
        """Test Controller class using Client with controller_token."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = (
            b'{"count": 1, "results": [{"id": 1, "name": "test"}]}'
        )
        mock_response.headers = {"content-type": "application/json"}
        mock_request_instance.open.return_value = mock_response

        # Create client and controller as modules would
        client = Client(
            host=token_module_params.get("controller_host"),
            token=token_module_params.get("controller_token"),
            timeout=token_module_params.get("request_timeout"),
            validate_certs=token_module_params.get("validate_certs"),
        )

        mock_module = create_mock_module(token_module_params)
        controller = Controller(client, mock_module)

        # Make a request through controller
        response = controller.get_endpoint("/test-endpoint")

        # Verify the request was made with token authentication
        mock_request_instance.open.assert_called_once()
        call_args = mock_request_instance.open.call_args

        headers = call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer test_token_123"

        assert response.status == 200

    def test_controller_token_validation_empty_token(self) -> None:
        """Test that empty controller_token is treated as no token."""
        params = {
            "controller_host": "https://aap.example.com",
            "controller_token": "",  # Empty string
            "controller_username": "testuser",
            "controller_password": "testpass",
        }

        with patch(
            "ansible_collections.ansible.eda.plugins.module_utils.client.Request"
        ):
            client = Client(
                host=params.get("controller_host"),
                username=params.get("controller_username"),
                password=params.get("controller_password"),
                token=params.get("controller_token"),
            )

            # Empty token should be falsy
            assert not client.token
            assert client.username == "testuser"
            assert client.password == "testpass"

    def test_controller_token_validation_none_token(self) -> None:
        """Test that None controller_token is handled correctly."""
        params = {
            "controller_host": "https://aap.example.com",
            "controller_token": None,
            "controller_username": "testuser",
            "controller_password": "testpass",
        }

        with patch(
            "ansible_collections.ansible.eda.plugins.module_utils.client.Request"
        ):
            client = Client(
                host=params.get("controller_host"),
                username=params.get("controller_username"),
                password=params.get("controller_password"),
                token=params.get("controller_token"),
            )

            assert client.token is None
            assert client.username == "testuser"
            assert client.password == "testpass"

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_authentication_error_handling(
        self, mock_request: Mock
    ) -> None:
        """Test error handling when controller_token authentication fails."""
        from http.client import HTTPMessage
        from urllib.error import HTTPError

        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        # Mock 401 authentication error
        http_error = HTTPError(
            url="https://aap.example.com/api/test",
            code=401,
            msg="Unauthorized",
            hdrs=HTTPMessage(),
            fp=None,
        )
        mock_request_instance.open.side_effect = http_error

        client = Client(host="https://aap.example.com", token="invalid_token_123")

        from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
            AuthError,
        )

        # Should raise AuthError for invalid token
        with pytest.raises(
            AuthError,
            match="Failed to authenticate with the instance: 401 Unauthorized",
        ):
            client.get("/test-endpoint")

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_url_building(self, mock_request: Mock) -> None:
        """Test that URL building works correctly with controller_token."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_response.headers = {"content-type": "application/json"}
        mock_request_instance.open.return_value = mock_response

        client = Client(host="https://aap.example.com", token="test_token_123")

        # Test different endpoint formats
        client.get("projects")
        client.get("/projects/")
        client.get("/api/eda/v1/projects/")

        # Verify all calls were made
        assert mock_request_instance.open.call_count == 3

        # Check that all calls had the correct Authorization header
        for call in mock_request_instance.open.call_args_list:
            headers = call.kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer test_token_123"

    def test_controller_token_module_integration_pattern(self) -> None:
        """Test the typical pattern of how modules use controller_token."""
        from ansible_collections.ansible.eda.plugins.module_utils.arguments import (  # type: ignore
            AUTH_ARGSPEC,
        )

        # Verify controller_token is in AUTH_ARGSPEC
        assert "controller_token" in AUTH_ARGSPEC
        token_spec = AUTH_ARGSPEC["controller_token"]

        # Verify it has the expected configuration
        assert token_spec["required"] is False
        assert token_spec["no_log"] is True
        assert "fallback" in token_spec

        # Check fallback environment variables
        fallback = token_spec["fallback"]
        assert fallback[0].__name__ == "env_fallback"  # env_fallback function
        env_vars = fallback[1]
        assert "CONTROLLER_TOKEN" in env_vars
        assert "AAP_TOKEN" in env_vars
        assert "AAP_OAUTH_TOKEN" in env_vars

    @patch("ansible_collections.ansible.eda.plugins.module_utils.client.Request")
    def test_controller_token_different_http_methods(self, mock_request: Mock) -> None:
        """Test controller_token authentication with different HTTP methods."""
        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        # Mock responses for different methods with correct status codes
        def mock_response_factory(status: int) -> Mock:
            response = Mock()
            response.status = status
            response.read.return_value = b'{"success": true}'
            response.headers = {"content-type": "application/json"}
            return response

        mock_request_instance.open.side_effect = [
            mock_response_factory(200),  # GET
            mock_response_factory(201),  # POST (expects 201, 202, or 204)
            mock_response_factory(200),  # PATCH (expects 200)
            mock_response_factory(204),  # DELETE (expects 204)
        ]

        client = Client(host="https://aap.example.com", token="test_token_123")

        # Test all HTTP methods
        client.get("/endpoint")
        client.post("/endpoint", data={"test": "data"})
        client.patch("/endpoint", data={"test": "data"})
        client.delete("/endpoint")

        # Verify all calls had correct Authorization header
        assert mock_request_instance.open.call_count == 4
        for call in mock_request_instance.open.call_args_list:
            headers = call.kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer test_token_123"
