#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: credential
author:
   - "Nikhil Jain (@jainnikhil30)"
   - "Alina Buzachis (@alinabuzachis)"
short_description: Manage credentials in EDA Controller
description:
    - This module allows the user to create, update or delete a credential in EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - Name of the credential.
    type: str
    required: true
  new_name:
    description:
      - Setting this option will change the existing name (lookup via name).
    type: str
  inputs:
    description:
      - Credential inputs where the keys are var names used in templating.
    type: dict
  credential_type_name:
    description:
      - The name of the credential type.
    type: str
  organization_name:
    description:
      - The name of the organization.
    type: int
    aliases:
      - org_name
  description:
    description:
      - Description of the credential.
    type: str
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
"""


EXAMPLES = """
- name: Create an EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    description: "Example credential description"
    inputs:
      field1: "field1"
    credential_type_name: "GitLab Personal Access Token"

- name: Delete an EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    state: absent
"""


RETURN = """
id:
  description: ID of the credential.
  returned: when exists
  type: int
  sample: 24
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def lookup(module, controller, endpoint, name):
    result = None
    try:
        result = controller.resolve_name_to_id(endpoint, name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to lookup resource: {e}")
    return result


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        inputs=dict(type="dict"),
        credential_type_name=dict(type="str"),
        organization_name=dict(type="int", aliases=["org_name"]),
        state=dict(choices=["present", "absent"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [("state", "present", ("name", "credential_type_name", "inputs"))]

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

    name = module.params.get("name")
    new_name = module.params.get("new_name")
    state = module.params.get("state")

    credential_params = {}
    if module.params.get("description"):
        credential_params["description"] = module.params["description"]

    if module.params.get("inputs"):
        credential_params["inputs"] = module.params["inputs"]

    credential_type_id = None
    if module.params.get("credential_type_name"):
        credential_type_id = lookup(
            module,
            controller,
            "credential-types",
            module.params["credential_type_name"],
        )

    if credential_type_id:
        credential_params["credential_type_id"] = credential_type_id

    organization_id = None
    if module.params.get("organization_id"):
        organization_id = lookup(
            module, controller, "organizations", module.params["organization_name"]
        )

    if organization_id:
        credential_params["organization_id"] = organization_id

    # Attempt to look up credential based on the provided name
    try:
        credential = controller.get_one_or_many("eda-credentials", name=name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get credential: {e}")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            result = controller.delete_if_needed(credential, endpoint="eda-credentials")
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete credential: {e}")

    credential_params["name"] = (
        new_name
        if new_name
        else (controller.get_item_name(credential) if credential else name)
    )

    # If the state was present and we can let the module build or update the
    # existing credential, this will return on its own
    try:
        result = controller.create_or_update_if_needed(
            credential,
            credential_params,
            endpoint="eda-credentials",
            item_type="credential",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update credential: {e}")


if __name__ == "__main__":
    main()
