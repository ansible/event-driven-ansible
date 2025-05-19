# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import env_fallback

AUTH_ARGSPEC: dict[str, dict[str, object]] = {
    "controller_host": {
        "fallback": (env_fallback, ["CONTROLLER_HOST", "AAP_HOSTNAME"]),
        "required": True,
        "aliases": ["aap_hostname"],
    },
    "controller_username": {
        "required": False,
        "fallback": (env_fallback, ["CONTROLLER_USERNAME", "AAP_USERNAME"]),
        "aliases": ["aap_username"],
    },
    "controller_password": {
        "required": False,
        "fallback": (env_fallback, ["CONTROLLER_PASSWORD", "AAP_PASSWORD"]),
        "no_log": True,
        "aliases": ["aap_password"],
    },
    "validate_certs": {
        "type": "bool",
        "default": True,
        "required": False,
        "fallback": (env_fallback, ["CONTROLLER_VERIFY_SSL", "AAP_VALIDATE_CERTS"]),
        "aliases": ["aap_validate_certs"],
    },
    "request_timeout": {
        "type": "float",
        "default": 10.0,
        "required": False,
        "fallback": (
            env_fallback,
            ["CONTROLLER_REQUEST_TIMEOUT", "AAP_REQUEST_TIMEOUT"],
        ),
        "aliases": ["aap_request_timeout"],
    },
}
