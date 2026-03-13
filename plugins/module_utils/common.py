# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule

from .controller import Controller
from .errors import EDAError


def lookup_resource_id(
    module: AnsibleModule,
    controller: Controller,
    endpoint: str,
    name: str,
    params: Optional[dict[str, Any]] = None,
) -> Optional[int]:
    result = None

    try:
        result = controller.resolve_name_to_id(
            endpoint, name, **params if params is not None else {}
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to lookup resource: {e}")
    return result


def handle_api_error(
    module: AnsibleModule,
    error: EDAError,
    new_params: list[str],
    min_version: str = "2.5",
) -> None:
    """
    Handle API errors and provide helpful messages for version incompatibilities.

    Args:
        module: AnsibleModule instance
        error: EDAError exception that was raised
        new_params: List of parameter names that require newer server versions
        min_version: Minimum EDA server version that supports these parameters

    Raises:
        Calls module.fail_json() with an appropriate error message
    """
    error_msg = str(error)

    # Check if error mentions any of the new parameters
    mentioned_params = [p for p in new_params if p in error_msg.lower()]

    # Common error patterns from Django REST framework for unknown fields
    unsupported_indicators = [
        "unknown field",
        "unexpected field",
        "not allowed",
        "invalid field",
        "unrecognized field",
    ]

    # If the error mentions new params and looks like a field validation error
    if mentioned_params and any(
        ind in error_msg.lower() for ind in unsupported_indicators
    ):
        module.fail_json(
            msg=(
                f"The EDA server does not support the following parameter(s): {','.join(mentioned_params)}. "
                f"These features require EDA server version {min_version} or later. "
                f"Please upgrade your EDA server, or remove these parameters from your task. "
                f"Original error: {error_msg}"
            )
        )
    else:
        # Not a version compatibility issue, fail with original error
        module.fail_json(msg=error_msg)
