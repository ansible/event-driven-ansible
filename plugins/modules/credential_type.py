#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: credential_type
author:
  - Alina Buzachis (@alinabuzachis)
short_description: Manage credential types in EDA Controller
description:
  - This module allows the user to create, update or delete a credential type in EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - The name of the credential type.
    type: str
    required: true
  description:
    description:
      - The description of the credential type to give more detail about it.
    type: str
  new_name:
    description:
      - Setting this option will change the existing name.
    type: str
  inputs:
    description:
      - Inputs of the credential type.
    type: dict
  injectors:
    description:
      - Injectors of the credential type.
    type: dict
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_type) supports AAP 2.5 and onwards.
"""


EXAMPLES = """
  - name: Create a credential type
    ansible.eda.credential_type:
      name: "Test"
      state: present
      description: "A test credential type"
      inputs:
        fields:
          - id: "Field1"
            type: "string"
            label: "Label1"
      injectors:
        extra_vars:
          field1: "field1"

  - name: Delete a credential type
    ansible.eda.credential_type:
      name: "Test"
      state: absent
"""


RETURN = """
id:
  description: ID of the credential type.
  returned: when exists
  type: int
  sample: 37
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        inputs=dict(type="dict"),
        injectors=dict(type="dict"),
        state=dict(choices=["present", "absent"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [("state", "present", ("inputs", "injectors"))]

    module = AnsibleModule(
        argument_spec=argument_spec, required_if=required_if, supports_check_mode=True
    )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    controller = Controller(client, module)
    credential_type_endpoint = "credential-types"
    credential_type_path = controller.get_endpoint(credential_type_endpoint)
    if credential_type_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.credential_type supports AAP 2.5 and onwards"
        )

    name = module.params.get("name")
    new_name = module.params.get("new_name")
    description = module.params.get("description")
    inputs = module.params.get("inputs")
    injectors = module.params.get("injectors")
    state = module.params.get("state")

    credential_type_params = {}
    if description:
        credential_type_params["description"] = description
    if inputs:
        credential_type_params["inputs"] = inputs
    if injectors:
        credential_type_params["injectors"] = injectors

    # Attempt to look up credential_type based on the provided name
    try:
        credential_type = controller.get_exactly_one(
            credential_type_endpoint, name=name
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get credential type: {e}")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            result = controller.delete_if_needed(
                credential_type, endpoint=credential_type_endpoint
            )
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete credential type: {e}")

    credential_type_params["name"] = (
        new_name
        if new_name
        else (controller.get_item_name(credential_type) if credential_type else name)
    )

    # If the state was present and we can let the module build or update the existing credential type,
    # this will return on its own
    try:
        result = controller.create_or_update_if_needed(
            credential_type,
            credential_type_params,
            endpoint=credential_type_endpoint,
            item_type="credential type",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update credential type: {e}")


if __name__ == "__main__":
    main()
