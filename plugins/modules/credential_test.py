#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_test
author:
  - "Generated for External SMS integration"
short_description: Test credential connectivity in EDA Controller
description:
    - This module allows testing credential connectivity, particularly for external Secret Management Systems (SMS).
    - Validates that the credential can successfully connect to and retrieve data from external systems.
version_added: 2.7.0
options:
  name:
    description:
      - Name of the credential to test.
    type: str
    required: true
  organization_name:
    description:
      - The name of the organization.
    type: str
  metadata:
    description:
      - Optional metadata for testing specific secrets or configurations.
      - The format depends on the credential type and external system.
    type: dict
    default: {}
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_test) supports AAP 2.5 and onwards.
  - This module is particularly useful for testing external SMS credentials like HashiCorp Vault, AWS Secrets Manager, etc.
  - The test does not modify any data, it only validates connectivity and access.
"""


EXAMPLES = r"""
- name: Test a HashiCorp Vault credential
  ansible.eda.credential_test:
    name: "HashiCorpVaultCred"
    organization_name: "Default"

- name: Test an AWS Secrets Manager credential with specific metadata
  ansible.eda.credential_test:
    name: "AWSSecretsManagerCred"
    metadata:
      secret_name: "test/secret"
    organization_name: "Default"

- name: Test a regular credential
  ansible.eda.credential_test:
    name: "SSHCredential"
    organization_name: "Default"
"""


RETURN = r"""
test_result:
  description: Result of the credential test.
  returned: always
  type: dict
  sample: {
    "success": true,
    "message": "Credential test successful",
    "details": {
      "connection_status": "connected",
      "test_timestamp": "2025-07-30T12:00:00.000000Z"
    }
  }
credential:
  description: Information about the tested credential.
  returned: always
  type: dict
  sample: {
    "id": 23,
    "name": "HashiCorpVaultCred",
    "credential_type": {
      "id": 45,
      "name": "HashiCorp Vault Secret Lookup",
      "namespace": "hashivault_kv"
    },
    "organization": {
      "id": 1,
      "name": "Default"
    }
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
            organization_name=dict(type="str"),
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
    
    credential_name = module.params.get("name")
    organization_name = module.params.get("organization_name")
    metadata = module.params.get("metadata", {})

    try:
        # Get organization ID if specified
        query_params = {}
        if organization_name:
            org_response = controller.get_endpoint("organizations/", name=organization_name)
            if org_response.status == 200 and org_response.json.get("results"):
                query_params["organization"] = org_response.json["results"][0]["id"]
            else:
                module.fail_json(msg=f"Organization '{organization_name}' not found")

        # Get credential
        cred_response = controller.get_endpoint("eda-credentials/", name=credential_name, **query_params)
        if cred_response.status != 200 or not cred_response.json.get("results"):
            module.fail_json(msg=f"Credential '{credential_name}' not found")
        
        credential = cred_response.json["results"][0]
        credential_id = credential["id"]

        # Test the credential
        test_data = {}
        if metadata:
            test_data["metadata"] = metadata

        if module.check_mode:
            # In check mode, just return success without actually testing
            controller.result.update({
                "test_result": {
                    "success": True,
                    "message": "Check mode - test would be performed",
                    "details": {"check_mode": True}
                },
                "credential": credential
            })
        else:
            # Perform actual test
            test_response = controller.post_endpoint(
                f"eda-credentials/{credential_id}/test/",
                data=test_data
            )
            
            if test_response.status == 200:
                controller.result.update({
                    "test_result": test_response.json,
                    "credential": credential
                })
            else:
                # Test failed
                error_msg = "Credential test failed"
                if test_response.json and isinstance(test_response.json, dict):
                    error_msg = test_response.json.get("message", error_msg)
                
                controller.result.update({
                    "test_result": {
                        "success": False,
                        "message": error_msg,
                        "details": test_response.json if test_response.json else {}
                    },
                    "credential": credential
                })

    except EDAError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**controller.result)


if __name__ == "__main__":
    main()