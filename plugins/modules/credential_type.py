#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing credential types in EDA Controller.

This module provides functionality to create, update, delete, or test
credential types in an Event-Driven Ansible controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_type
author:
  - Alina Buzachis (@alinabuzachis)
short_description: Manage credential types in EDA Controller
description:
  - This module allows the user to create, update, delete, or test a credential type in EDA controller.
  - When using state 'test', the module validates credential type configuration and input schemas without
    making changes.
  - Testing is particularly useful for verifying external secret management system credential type definitions.
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
  test_inputs:
    description:
      - Input values to test with the credential type
      - Only used when state is 'test'
      - Should match the credential type's input schema and required fields
      - Used to validate that the credential type can accept and process these input values
    required: false
    type: dict
  test_metadata:
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
      - C(present) - Create or update the credential type
      - C(absent) - Remove the credential type
      - C(test) - Test the credential type configuration without making any changes
    default: "present"
    choices: ["present", "absent", "test"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_type) supports AAP 2.5 and onwards.
  - The C(test) state validates credential type configuration without making any changes and always
    returns C(changed=False).
  - Testing validates the credential type's input schema and configuration with sample values.
  - The C(test_inputs) and C(test_metadata) parameters are only used with C(state=test) for validation.
"""


EXAMPLES = r"""
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

- name: Test a HashiCorp Vault credential type configuration
  ansible.eda.credential_type:
    name: "HashiCorp Vault Secret Lookup"
    state: test
    test_inputs:
      url: "https://vault.example.com:8200/"
      token: "dummy-token-for-testing"
      api_version: "v2"
    test_metadata:
      secret_path: "secret/myapp"
      secret_key: "password"

- name: Test credential type basic configuration
  ansible.eda.credential_type:
    name: "AWS Secrets Manager lookup"
    state: test
"""


RETURN = r"""
id:
  description: ID of the credential type.
  returned: when exists
  type: int
  sample: 37
test_result:
  description: Result of the credential type test.
  returned: when state is 'test'
  type: dict
  contains:
    success:
      description: Whether the credential type test was successful.
      type: bool
      sample: true
    message:
      description: Human-readable message describing the test result.
      type: str
      sample: "Credential type test successful"
    details:
      description: Additional details about the test result or error information.
      type: dict
      returned: when additional information is available
  sample: {
    "success": true,
    "message": "Credential type test successful"
  }
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    """Main entry point for the credential_type module.

    Manages credential types in EDA controller by creating, updating, deleting,
    or testing them based on the provided parameters and desired state.

    :raises: AnsibleModule.fail_json on errors during credential type operations
    :returns: None
    :rtype: None
    """
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        inputs=dict(type="dict"),
        injectors=dict(type="dict"),
        test_inputs=dict(type="dict"),
        test_metadata=dict(type="dict"),
        state=dict(choices=["present", "absent", "test"], default="present"),
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
        token=module.params.get("controller_token"),
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
    test_inputs = module.params.get("test_inputs")
    test_metadata = module.params.get("test_metadata")
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

    if state == "test":

        if not credential_type:
            module.fail_json(msg=f"Credential type '{name}' not found")

        test_data = {}
        if test_inputs:
            test_data["inputs"] = test_inputs
        if test_metadata:
            test_data["metadata"] = test_metadata

        if module.check_mode:
            test_result = {
                "success": True,
                "message": "Check mode - test would be performed",
                "details": {"check_mode": True},
            }
            module.exit_json(changed=False, test_result=test_result)

        try:
            test_response = controller.post_endpoint(
                f"credential-types/{credential_type['id']}/test/", data=test_data
            )

            if test_response.status in [200, 202]:
                if test_response.json:
                    test_result = test_response.json
                else:
                    test_result = {
                        "success": True,
                        "message": f"HTTP {test_response.status}: Credential type test accepted",
                        "details": {"status": test_response.status},
                    }
            else:
                error_msg = "Credential type test failed"
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
            module.fail_json(msg=f"Failed to test credential type: {e}")

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
