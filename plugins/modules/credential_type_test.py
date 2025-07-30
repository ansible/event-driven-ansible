#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_type_test
author:
  - "Generated for External SMS integration"
short_description: Test credential type configuration in EDA Controller
description:
    - This module allows testing credential type configuration, particularly for external Secret Management Systems (SMS).
    - Validates that the credential type is properly configured and can be used to create working credentials.
version_added: 2.7.0
options:
  name:
    description:
      - Name of the credential type to test.
    type: str
    required: true
  inputs:
    description:
      - Input values to test with the credential type.
      - Should match the credential type's input schema.
    type: dict
    default: {}
  metadata:
    description:
      - Optional metadata for testing specific configurations.
      - The format depends on the credential type and external system.
    type: dict
    default: {}
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_type_test) supports AAP 2.5 and onwards.
  - This module is particularly useful for testing external SMS credential types like HashiCorp Vault, AWS Secrets Manager, etc.
  - The test does not modify any data, it only validates the credential type configuration.
"""


EXAMPLES = r"""
- name: Test a HashiCorp Vault credential type
  ansible.eda.credential_type_test:
    name: "HashiCorp Vault Secret Lookup"
    inputs:
      url: "https://vault.example.com:8200"
      token: "hvs.test-token"
      cacert: ""

- name: Test an AWS Secrets Manager credential type
  ansible.eda.credential_type_test:
    name: "AWS Secrets Manager lookup"
    inputs:
      access_key: "AKIA..."
      secret_key: "test-secret-key"
      region: "us-east-1"

- name: Test a credential type with metadata
  ansible.eda.credential_type_test:
    name: "Azure Key Vault"
    inputs:
      url: "https://keyvault.vault.azure.net/"
      client_id: "client-id"
      secret: "client-secret"
      tenant: "tenant-id"
    metadata:
      secret_name: "test-secret"
"""


RETURN = r"""
test_result:
  description: Result of the credential type test.
  returned: always
  type: dict
  sample: {
    "success": true,
    "message": "Credential type test successful",
    "details": {
      "validation_status": "valid",
      "test_timestamp": "2025-07-30T12:00:00.000000Z"
    }
  }
credential_type:
  description: Information about the tested credential type.
  returned: always
  type: dict
  sample: {
    "id": 45,
    "name": "HashiCorp Vault Secret Lookup",
    "namespace": "hashivault_kv",
    "kind": "external",
    "description": "HashiCorp Vault Secret Lookup credential type"
  }
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import ControllerArgs
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = ControllerArgs.common_args()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            inputs=dict(type="dict", default={}),
            metadata=dict(type="dict", default={}),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    client = Client(
        host=module.params.get("aap_hostname"),
        username=module.params.get("aap_username"),
        password=module.params.get("aap_password"),
        timeout=module.params.get("aap_timeout"),
        validate_certs=module.params.get("aap_validate_certs"),
    )

    controller = Controller(client, module)

    credential_type_name = module.params.get("name")
    inputs = module.params.get("inputs", {})
    metadata = module.params.get("metadata", {})

    try:
        # Get credential type
        cred_type_response = controller.get_endpoint(
            "credential-types/", name=credential_type_name
        )
        if cred_type_response.status != 200 or not cred_type_response.json.get(
            "results"
        ):
            module.fail_json(msg=f"Credential type '{credential_type_name}' not found")

        credential_type = cred_type_response.json["results"][0]
        credential_type_id = credential_type["id"]

        # Test the credential type
        test_data = {}
        if inputs:
            test_data["inputs"] = inputs
        if metadata:
            test_data["metadata"] = metadata

        if module.check_mode:
            # In check mode, just return success without actually testing
            controller.result.update(
                {
                    "test_result": {
                        "success": True,
                        "message": "Check mode - test would be performed",
                        "details": {"check_mode": True},
                    },
                    "credential_type": credential_type,
                }
            )
        else:
            # Perform actual test
            test_response = controller.post_endpoint(
                f"credential-types/{credential_type_id}/test/", data=test_data
            )

            if test_response.status == 200:
                controller.result.update(
                    {
                        "test_result": test_response.json,
                        "credential_type": credential_type,
                    }
                )
            else:
                # Test failed
                error_msg = "Credential type test failed"
                if test_response.json and isinstance(test_response.json, dict):
                    error_msg = test_response.json.get("message", error_msg)

                controller.result.update(
                    {
                        "test_result": {
                            "success": False,
                            "message": error_msg,
                            "details": test_response.json if test_response.json else {},
                        },
                        "credential_type": credential_type,
                    }
                )

    except EDAError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**controller.result)


if __name__ == "__main__":
    main()
