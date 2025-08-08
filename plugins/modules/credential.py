#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential
author:
   - "Nikhil Jain (@jainnikhil30)"
   - "Alina Buzachis (@alinabuzachis)"
short_description: Manage credentials in EDA Controller
description:
    - This module allows the user to create, update, delete, or test a credential in EDA controller.
    - When using state 'test', the module validates credential connectivity to external systems without making changes.
    - Testing is particularly useful for verifying external secret management system credentials.
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
  copy_from:
    description:
      - Name of the existing credential to copy.
      - If set, copies the specified credential.
      - The new credential will be created with the name given in the C(name) parameter.
    type: str
    version_added: '2.6.0'
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
    type: str
    aliases:
      - organization
  description:
    description:
      - Description of the credential.
    type: str
  metadata:
    description:
      - Additional configuration for testing specific secrets or configurations
      - Only used when state is 'test'
      - The structure depends on the credential type and external system
      - For HashiCorp Vault, should include keys like 'secret_path' and 'secret_key'
    required: false
    type: dict
  state:
    description:
      - Desired state of the resource.
      - C(present) - Create or update the credential
      - C(absent) - Remove the credential
      - C(test) - Test the credential connectivity without making any changes
    default: "present"
    choices: ["present", "absent", "test"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential) supports AAP 2.5 and onwards.
  - The C(test) state validates credential connectivity without making any changes and always returns C(changed=False).
  - Testing supports external secret management systems and requires the credential to already exist.
  - The C(metadata) parameter is only used with C(state=test) to specify test-specific configurations.
"""


EXAMPLES = r"""
- name: Create an EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    description: "Example credential description"
    inputs:
      field1: "field1"
    credential_type_name: "GitLab Personal Access Token"
    organization_name: Default

- name: Delete an EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    state: absent

- name: Copy an existing EDA Credential
  ansible.eda.credential:
    name: "New Copied Credential"
    copy_from: "Existing Credential"

- name: Test a HashiCorp Vault credential connectivity
  ansible.eda.credential:
    name: "vault_lookup_credential"
    state: test
    metadata:
      secret_path: "secret/myapp"
      secret_key: "password"
    organization_name: Default

- name: Test credential basic connectivity
  ansible.eda.credential:
    name: "my_aws_credential"
    state: test
    organization_name: Default
"""


RETURN = r"""
id:
  description: ID of the credential.
  returned: when exists
  type: int
  sample: 24
test_result:
  description: Result of the credential test.
  returned: when state is 'test'
  type: dict
  contains:
    success:
      description: Whether the credential test was successful.
      type: bool
      sample: true
    message:
      description: Human-readable message describing the test result.
      type: str
      sample: "Credential test successful"
    details:
      description: Additional details about the test result or error information.
      type: dict
      returned: when additional information is available
  sample: {
    "success": true,
    "message": "Credential test successful"
  }
"""


from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def create_params(module: AnsibleModule, controller: Controller) -> dict[str, Any]:
    credential_params: dict[str, Any] = {}

    credential_params = {}
    if module.params.get("description"):
        credential_params["description"] = module.params["description"]

    if module.params.get("inputs"):
        credential_params["inputs"] = module.params["inputs"]

    credential_type_id = None
    if module.params.get("credential_type_name"):
        credential_type_id = lookup_resource_id(
            module,
            controller,
            "credential-types",
            module.params["credential_type_name"],
        )

    if credential_type_id:
        credential_params["credential_type_id"] = credential_type_id

    organization_id = None
    if module.params.get("organization_name"):
        organization_id = lookup_resource_id(
            module, controller, "organizations", module.params["organization_name"]
        )

    if organization_id:
        credential_params["organization_id"] = organization_id

    return credential_params


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        copy_from=dict(type="str"),
        description=dict(type="str"),
        inputs=dict(type="dict"),
        credential_type_name=dict(type="str"),
        organization_name=dict(type="str", aliases=["organization"]),
        metadata=dict(type="dict"),
        state=dict(choices=["present", "absent", "test"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    copy_from = module.params.get("copy_from", None)

    required_if = []
    if not copy_from:
        required_if = [
            (
                "state",
                "present",
                ("name", "credential_type_name", "inputs", "organization_name"),
            )
        ]

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
    credential_endpoint = "eda-credentials"
    credential_path = controller.get_endpoint(credential_endpoint)
    if credential_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.credential supports AAP 2.5 and onwards"
        )

    name = module.params.get("name")
    new_name = module.params.get("new_name")
    state = module.params.get("state")

    # Attempt to look up credential based on the provided name
    try:
        credential = controller.get_exactly_one(
            credential_endpoint, name=copy_from if copy_from else name
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get credential: {e}")

    if state == "test":
        if not credential:
            module.fail_json(msg=f"Credential '{name}' not found")

        metadata = module.params.get("metadata", {})
        test_data = {"metadata": metadata} if metadata else {}

        if module.check_mode:
            test_result = {
                "success": True,
                "message": "Check mode - test would be performed",
                "details": {"check_mode": True},
            }
            module.exit_json(changed=False, test_result=test_result)

        try:
            test_response = controller.post_endpoint(
                f"eda-credentials/{credential['id']}/test/", data=test_data
            )

            if test_response.status in [200, 202]:
                if test_response.json:
                    test_result = test_response.json
                else:
                    test_result = {
                        "success": True,
                        "message": f"HTTP {test_response.status}: Credential test accepted",
                        "details": {"status": test_response.status},
                    }
            else:
                error_msg = "Credential test failed"
                if test_response.json and isinstance(test_response.json, dict):
                    error_msg = test_response.json.get("message", error_msg)
                elif test_response.data:
                    error_msg = f"HTTP {test_response.status}: {test_response.data}"

                test_result = {
                    "success": False,
                    "message": error_msg,
                    "details": (
                        test_response.json
                        if test_response.json
                        else {"status": test_response.status}
                    ),
                }

            module.exit_json(changed=False, test_result=test_result)

        except EDAError as e:
            module.fail_json(msg=f"Failed to test credential: {e}")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            result = controller.delete_if_needed(
                credential, endpoint=credential_endpoint
            )
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete credential: {e}")

    # Activation Data that will be sent for create/update
    credential_params = create_params(module, controller)
    credential_params["name"] = (
        new_name
        if new_name
        else (controller.get_item_name(credential) if credential else name)
    )

    # we attempt to copy only when copy_from is passed
    if copy_from:
        try:
            result = controller.copy_if_needed(
                name,
                copy_from,
                endpoint=f"eda-credentials/{credential['id']}/copy",
                item_type="credential",
            )
            module.exit_json(changed=True)
        except KeyError as e:
            module.fail_json(
                msg=f"Unable to access {e} of the credential to copy from."
            )
        except EDAError as e:
            module.fail_json(msg=f"Failed to copy credential: {e}")

    # If the state was present and we can let the module build or update the
    # existing credential, this will return on its own
    try:
        result = controller.create_or_update_if_needed(
            credential,
            credential_params,
            endpoint=credential_endpoint,
            item_type="credential",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update credential: {e}")


if __name__ == "__main__":
    main()
