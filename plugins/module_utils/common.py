# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Common utilities for Event-Driven Ansible modules.

This module contains helper functions used by various EDA modules
for common operations.
"""

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
    """Look up a resource ID by its name.

    Searches for a resource at the specified controller API endpoint
    by name and returns its ID. In case of error, fails the module
    with an error message.

    :param module: Ansible module instance for error output
    :param controller: Controller instance for executing requests
    :param endpoint: API endpoint for resource lookup
    :param name: Resource name to search for
    :param params: Additional parameters for the search (optional)
    :returns: ID of the found resource or None if not found
    :raises: Module fails with error via module.fail_json on EDAError
    """
    result = None

    try:
        result = controller.resolve_name_to_id(
            endpoint, name, **params if params is not None else {}
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to lookup resource: {e}")
    return result
