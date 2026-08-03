
# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)




from typing import Any

from ansible.module_utils.basic import AnsibleModule

from .controller import Controller
from .errors import EDAError


def lookup_resource_id(
    module: AnsibleModule,
    controller: Controller,
    endpoint: str,
    name: str,
    params: dict[str, Any] | None = None,
) -> int | None:
    result = None

    try:
        result = controller.resolve_name_to_id(
            endpoint, name, **params if params is not None else {}
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to lookup resource: {e}")
    return result
