# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""HTTP client for interacting with Event-Driven Ansible API.

This module provides classes for making HTTP requests
to the Event-Driven Ansible controller with authentication
and error handling.
"""

from __future__ import absolute_import, division, print_function

from typing import Any, Optional

__metaclass__ = type

import json
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urlencode, urlparse

from ansible.module_utils.urls import Request

from .errors import AuthError, EDAHTTPError


class Response:
    """Class representing an HTTP response from EDA API.

    Encapsulates HTTP response data including status,
    content, and headers. Provides convenient access to JSON data.
    """

    def __init__(self, status: int, data: str, headers: Optional[Any] = None) -> None:
        """Initialize the response object.

        :param status: HTTP status code of the response
        :type status: int
        :param data: Response body as a string
        :type data: str
        :param headers: HTTP response headers (optional)
        :type headers: Optional[Any]
        """
        self.status = status
        self.data = data
        # [('h1', 'v1'), ('H2', 'V2')] -> {'h1': 'v1', 'h2': 'V2'}
        self.headers = (
            dict((k.lower(), v) for k, v in dict(headers).items()) if headers else {}
        )

        self._json = None

    @property
    def json(self) -> Any:
        """Get the response content as JSON.

        Parses the response body as JSON and caches the result.
        On subsequent calls, returns the cached value.

        :returns: Parsed JSON data
        :rtype: Any
        :raises EDAHTTPError: If the data is not valid JSON
        """
        if self._json is None:
            try:
                self._json = json.loads(self.data)
            except ValueError as value_exp:
                raise EDAHTTPError(
                    f"Received invalid JSON response: {self.data}"
                ) from value_exp
        return self._json


class Client:
    """HTTP client for interacting with Event-Driven Ansible API.

    Provides methods for making HTTP requests to the EDA controller
    with support for various authentication methods (token or username/password).
    """

    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[Any] = None,
        validate_certs: Optional[Any] = None,
    ) -> None:
        """Initialize the HTTP client.

        :param host: EDA controller host (with or without protocol)
        :type host: str
        :param username: Username for authentication (optional)
        :type username: Optional[str]
        :param password: Password for authentication (optional)
        :type password: Optional[str]
        :param token: Token for authentication (optional)
        :type token: Optional[str]
        :param timeout: Timeout for HTTP requests (optional)
        :type timeout: Optional[Any]
        :param validate_certs: Whether to validate SSL certificates (optional)
        :type validate_certs: Optional[Any]
        :raises ValueError: If host is empty
        :raises EDAHTTPError: If unable to parse the host URL
        """
        if not host:
            raise ValueError("Host must be a non-empty string.")

        if not host.startswith(("https://", "http://")):
            self.host = f"https://{host}"
        else:
            self.host = host

        self.username = username
        self.password = password
        self.timeout = timeout
        self.validate_certs = validate_certs
        self.token = token

        # Try to parse the hostname as a url
        try:
            self.url = urlparse(self.host)
            # Store URL prefix for later use in build_url
            self.url_prefix = self.url.path
        except Exception as e:
            raise EDAHTTPError(
                f"Unable to parse eda_controller_host ({self.host}): {e}"
            ) from e

        self.session = Request()

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
    ) -> Response:
        """Execute an HTTP request to the API.

        Internal method for making HTTP requests with authentication
        and error handling.

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        :type method: str
        :param path: Full URL path for the request
        :type path: str
        :param data: Data to send in the request body (optional)
        :type data: Optional[Any]
        :param headers: HTTP headers for the request (optional)
        :type headers: Optional[Any]
        :returns: Response object with request results
        :rtype: Response
        :raises AuthError: On authentication error (HTTP 401)
        :raises EDAHTTPError: On network or URL errors
        """
        try:
            raw_resp = self.session.open(
                method,
                path,
                data=data,
                url_password=self.password if not self.token else None,
                url_username=self.username if not self.token else None,
                headers=headers,
                timeout=self.timeout,
                validate_certs=self.validate_certs,
                force_basic_auth=True,
            )

        except HTTPError as http_exp:
            # Wrong username/password, or expired access token
            if http_exp.code == 401:
                raise AuthError(
                    f"Failed to authenticate with the instance: {http_exp.code} {http_exp.reason}"
                ) from http_exp
            # Other HTTP error codes do not necessarily mean errors.
            # This is for the caller to decide.
            return Response(
                http_exp.code, http_exp.read().decode("utf-8"), http_exp.headers
            )
        except URLError as url_exp:
            raise EDAHTTPError(url_exp.reason) from url_exp

        return Response(raw_resp.status, raw_resp.read(), raw_resp.headers)

    def build_url(
        self,
        endpoint: str,
        query_params: Optional[Any] = None,
        identifier: Optional[Any] = None,
    ) -> ParseResult:
        """Build a full URL for an API endpoint.

        Constructs a full URL from the endpoint, adding API prefix,
        query parameters, and resource identifier as needed.

        :param endpoint: API endpoint (can be relative or full)
        :type endpoint: str
        :param query_params: Query parameters to add to the URL (optional)
        :type query_params: Optional[Any]
        :param identifier: Resource ID to add to the path (optional)
        :type identifier: Optional[Any]
        :returns: Parsed URL object
        :rtype: ParseResult
        """
        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        prefix = self.url_prefix.rstrip("/")

        if not endpoint.startswith(prefix + "/api/"):
            endpoint = prefix + f"/api/eda/v1{endpoint}"
        if not endpoint.endswith("/") and "?" not in endpoint:
            endpoint = f"{endpoint}/"

        # Update the URL path with the endpoint
        url = self.url._replace(path=endpoint)

        if query_params:
            url = url._replace(query=urlencode(query_params))
        if identifier:
            url = url._replace(path=url.path + str(identifier) + "/")

        return url

    def request(self, method: str, endpoint: str, **kwargs: Any) -> Response:
        """Execute an HTTP request to the specified endpoint.

        Main method for making API requests with automatic
        URL, header, and data handling based on the method.

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        :type method: str
        :param endpoint: API endpoint for the request
        :type endpoint: str
        :param kwargs: Additional parameters (data, headers, id)
        :type kwargs: Any
        :returns: Response object with request results
        :rtype: Response
        :raises EDAHTTPError: If HTTP method is not specified
        """
        # In case someone is calling us directly; make sure we were given a
        # method, let's not just assume a GET
        if not method:
            raise EDAHTTPError("The HTTP method must be defined")

        if method in ["POST"]:
            url = self.build_url(endpoint)
        elif method in ["DELETE", "PATCH", "PUT"]:
            url = self.build_url(endpoint, identifier=kwargs.get("id"))
        else:
            url = self.build_url(endpoint, query_params=kwargs.get("data"))

        # Extract the headers, this will be used in a couple of places
        headers: dict[str, str] = kwargs.get("headers", {})

        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        if method in ["POST", "PUT", "PATCH"]:
            headers.setdefault("Content-Type", "application/json")
            kwargs["headers"] = headers

        data = (
            None  # Important, if content type is not JSON, this should not
            # be dict type
        )
        if headers.get("Content-Type", "") == "application/json":
            data = json.dumps(kwargs.get("data", {}))

        return self._request(method, url.geturl(), data=data, headers=headers)

    def get(self, path: str, **kwargs: str) -> Response:
        """Execute a GET request.

        :param path: API endpoint for the GET request
        :type path: str
        :param kwargs: Additional request parameters
        :type kwargs: str
        :returns: Response object
        :rtype: Response
        :raises EDAHTTPError: If response status is not 200 or 404
        """
        resp = self.request("GET", path, **kwargs)
        if resp.status in (200, 404):
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def post(self, path: str, **kwargs: Any) -> Response:
        """Execute a POST request.

        :param path: API endpoint for the POST request
        :type path: str
        :param kwargs: Additional request parameters (data, headers)
        :type kwargs: Any
        :returns: Response object
        :rtype: Response
        :raises EDAHTTPError: If response status is not 201, 202, or 204
        """
        resp = self.request("POST", path, **kwargs)
        if resp.status in [201, 202, 204]:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def patch(self, path: str, **kwargs: Any) -> Response:
        """Execute a PATCH request.

        :param path: API endpoint for the PATCH request
        :type path: str
        :param kwargs: Additional request parameters (data, headers, id)
        :type kwargs: Any
        :returns: Response object
        :rtype: Response
        :raises EDAHTTPError: If response status is not 200
        """
        resp = self.request("PATCH", path, **kwargs)
        if resp.status == 200:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def delete(self, path: str, **kwargs: Any) -> Response:
        """Execute a DELETE request.

        :param path: API endpoint for the DELETE request
        :type path: str
        :param kwargs: Additional request parameters (id)
        :type kwargs: Any
        :returns: Response object
        :rtype: Response
        :raises EDAHTTPError: If response status is not 204
        """
        resp = self.request("DELETE", path, **kwargs)
        if resp.status == 204:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")
