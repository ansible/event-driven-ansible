# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def lookup_resource_id(
    module: AnsibleModule,
    controller: Controller,
    endpoint: str,
    name: str,
    params: Optional[dict[str, Any]] = None,
):
    result = None

    try:
        result = controller.resolve_name_to_id(
            endpoint, name, **params if params is not None else {}
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to lookup resource: {e}")
    return result
