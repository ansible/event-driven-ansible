# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import env_fallback

AUTH_ARGSPEC: dict[str, dict[str, object]] = {
    "controller_host": {
        "fallback": (env_fallback, ["CONTROLLER_HOST"]),
        "required": True,
    },
    "controller_username": {
        "fallback": (env_fallback, ["CONTROLLER_USERNAME"]),
    },
    "controller_password": {
        "fallback": (env_fallback, ["CONTROLLER_PASSWORD"]),
        "no_log": True,
    },
    "validate_certs": {
        "type": "bool",
        "default": True,
        "fallback": (env_fallback, ["CONTROLLER_VERIFY_SSL"]),
    },
    "request_timeout": {
        "type": "float",
        "default": 10.0,
        "fallback": (env_fallback, ["CONTROLLER_REQUEST_TIMEOUT"]),
    },
}
