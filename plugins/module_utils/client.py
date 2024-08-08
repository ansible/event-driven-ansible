# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode

from ansible.module_utils.urls import Request

from .errors import AuthError, EDAHTTPError


class Response:
    def __init__(self, status, data, headers=None):
        self.status = status
        self.data = data
        # [('h1', 'v1'), ('H2', 'V2')] -> {'h1': 'v1', 'h2': 'V2'}
        self.headers = (
            dict((k.lower(), v) for k, v in dict(headers).items()) if headers else {}
        )

        self._json = None

    @property
    def json(self):
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
        host,
        username=None,
        password=None,
        timeout=None,
        validate_certs=None,
    ):
        if not (host or "").startswith(("https://", "http://")):
            raise EDAHTTPError(
                f"Invalid instance host value: '{host}'. "
                "Value must start with 'https://' or 'http://'"
            )

        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.validate_certs = validate_certs

        self._client = Request()

    def _request(self, method, path, data=None, headers=None):
        try:
            raw_resp = self._client.open(
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
            return Response(http_exp.code, http_exp.read(), http_exp.headers)
        except URLError as url_exp:
            raise EDAHTTPError(url_exp.reason) from url_exp

        return Response(raw_resp.status, raw_resp.read(), raw_resp.headers)

    def request(self, method, path, query=None, data=None, headers=None):
        escaped_path = quote(path.strip("/"))
        if escaped_path:
            escaped_path = "/" + escaped_path
        url = f"{self.host}{escaped_path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        return self._request(method, url, data=data, headers=headers)

    def get(self, path, query=None):
        resp = self.request("GET", path, query=query)
        if resp.status in (200, 404):
            return resp
        raise EDAHTTPError("HTTP ERROR")

    def post(self, path, data, query=None):
        raise NotImplementedError()

    def patch(self, path, data, query=None):
        raise NotImplementedError()

    def put(self, path, data, query=None):
        raise NotImplementedError()

    def delete(self, path, query=None):
        raise NotImplementedError()
