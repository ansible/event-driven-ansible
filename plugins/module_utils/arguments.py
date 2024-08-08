# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from ansible.module_utils.basic import env_fallback

AUTH_ARGSPEC = dict(
    controller_host=dict(
        fallback=(env_fallback, ["CONTROLLER_HOST"]),
    ),
    controller_username=dict(
        fallback=(env_fallback, ["CONTROLLER_USERNAME"]),
    ),
    controller_password=dict(
        no_log=True,
        fallback=(env_fallback, ["CONTROLLER_PASSWORD"]),
    ),
    validate_certs=dict(
        type="bool",
        fallback=(env_fallback, ["CONTROLLER_VERIFY_SSL"]),
    ),
    request_timeout=dict(
        type="float",
        fallback=(env_fallback, ["CONTROLLER_REQUEST_TIMEOUT"]),
        default=10.0,
    ),
)
