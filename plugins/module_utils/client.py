# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

from typing import Any, Optional

__metaclass__ = type

import json
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urlencode, urlparse

from ansible.module_utils.urls import Request

from .errors import AuthError, EDAHTTPError


class Response:
    def __init__(self, status: int, data: str, headers: Optional[Any] = None) -> None:
        self.status = status
        self.data = data
        # [('h1', 'v1'), ('H2', 'V2')] -> {'h1': 'v1', 'h2': 'V2'}
        self.headers = (
            dict((k.lower(), v) for k, v in dict(headers).items()) if headers else {}
        )

        self._json = None

    @property
    def json(self) -> Any:
        if self._json is None:
            try:
                self._json = json.loads(self.data)
            except ValueError as value_exp:
                raise EDAHTTPError(
                    f"Received invalid JSON response: {self.data}"
                ) from value_exp
        return self._json


class Client:
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[Any] = None,
        validate_certs: Optional[Any] = None,
    ) -> None:
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
        try:
            raw_resp = self.session.open(
                method,
                path,
                data=data,
                url_password=self.password,
                url_username=self.username,
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
        resp = self.request("GET", path, **kwargs)
        if resp.status in (200, 404):
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def post(self, path: str, **kwargs: Any) -> Response:
        resp = self.request("POST", path, **kwargs)
        if resp.status in [201, 202, 204]:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def patch(self, path: str, **kwargs: Any) -> Response:
        resp = self.request("PATCH", path, **kwargs)
        if resp.status == 200:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")

    def delete(self, path: str, **kwargs: Any) -> Response:
        resp = self.request("DELETE", path, **kwargs)
        if resp.status == 204:
            return resp
        raise EDAHTTPError(f"HTTP error {resp.json}")
