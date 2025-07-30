#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_input_source_info
author:
  - "Generated for External SMS integration"
short_description: List credential input sources in the EDA Controller
description:
    - List credential input sources in the EDA controller.
    - Credential input sources link credential fields to external Secret Management Systems (SMS).
version_added: 2.7.0
options:
  target_credential_name:
    description:
      - Name of the target credential to filter input sources by.
      - If specified, only input sources for this credential will be returned.
    type: str
    required: false
  source_credential_name:
    description:
      - Name of the source credential to filter input sources by.
      - If specified, only input sources using this external credential will be returned.
    type: str
    required: false
  input_field_name:
    description:
      - Name of the input field to filter by.
      - If specified, only input sources for this field will be returned.
    type: str
    required: false
  organization_name:
    description:
      - The name of the organization to filter by.
    type: str
    required: false
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_input_source_info) supports AAP 2.5 and onwards.
"""


EXAMPLES = r"""
- name: Get information about all credential input sources
  ansible.eda.credential_input_source_info:

- name: Get input sources for a specific target credential
  ansible.eda.credential_input_source_info:
    target_credential_name: "MyAppCredential"

- name: Get input sources using a specific external credential
  ansible.eda.credential_input_source_info:
    source_credential_name: "HashiCorpVaultCred"

- name: Get input sources for a specific field
  ansible.eda.credential_input_source_info:
    input_field_name: "password"

- name: Get input sources in a specific organization
  ansible.eda.credential_input_source_info:
    organization_name: "Production"
"""


RETURN = r"""
credential_input_sources:
  description: Information about credential input sources.
  returned: always
  type: list
  elements: dict
  sample: [
    {
      "id": 37,
      "description": "Link password field to HashiCorp Vault",
      "created_at": "2025-07-30T12:00:00.000000Z",
      "modified_at": "2025-07-30T12:00:00.000000Z",
      "target_credential": {
        "id": 15,
        "name": "MyAppCredential",
        "credential_type": {
          "id": 2,
          "name": "Machine",
          "namespace": "machine"
        }
      },
      "source_credential": {
        "id": 23,
        "name": "HashiCorpVaultCred",
        "credential_type": {
          "id": 45,
          "name": "HashiCorp Vault Secret Lookup",
          "namespace": "hashivault_kv"
        }
      },
      "input_field_name": "password",
      "metadata": {
        "secret_path": "secret/myapp",
        "secret_key": "password"
      },
      "organization": {
        "id": 1,
        "name": "Default"
      }
    }
  ]
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
            target_credential_name=dict(type="str", required=False),
            source_credential_name=dict(type="str", required=False),
            input_field_name=dict(type="str", required=False),
            organization_name=dict(type="str", required=False),
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

    target_credential_name = module.params.get("target_credential_name")
    source_credential_name = module.params.get("source_credential_name")
    input_field_name = module.params.get("input_field_name")
    organization_name = module.params.get("organization_name")

    try:
        # Build query parameters for filtering
        query_params = {}

        # Filter by target credential
        if target_credential_name:
            target_cred_response = controller.get_endpoint(
                "eda-credentials/", name=target_credential_name
            )
            if target_cred_response.status == 200 and target_cred_response.json.get(
                "results"
            ):
                query_params["target_credential"] = target_cred_response.json[
                    "results"
                ][0]["id"]
            else:
                module.fail_json(
                    msg=f"Target credential '{target_credential_name}' not found"
                )

        # Filter by source credential
        if source_credential_name:
            source_cred_response = controller.get_endpoint(
                "eda-credentials/", name=source_credential_name
            )
            if source_cred_response.status == 200 and source_cred_response.json.get(
                "results"
            ):
                query_params["source_credential"] = source_cred_response.json[
                    "results"
                ][0]["id"]
            else:
                module.fail_json(
                    msg=f"Source credential '{source_credential_name}' not found"
                )

        # Filter by input field name
        if input_field_name:
            query_params["input_field_name"] = input_field_name

        # Filter by organization
        if organization_name:
            org_response = controller.get_endpoint(
                "organizations/", name=organization_name
            )
            if org_response.status == 200 and org_response.json.get("results"):
                query_params["organization"] = org_response.json["results"][0]["id"]
            else:
                module.fail_json(msg=f"Organization '{organization_name}' not found")

        # Get credential input sources
        response = controller.get_endpoint("credential-input-sources/", **query_params)

        if response.status == 200:
            controller.result["credential_input_sources"] = response.json.get(
                "results", []
            )
        else:
            raise EDAError(
                f"Failed to retrieve credential input sources: {response.text}"
            )

    except EDAError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**controller.result)


if __name__ == "__main__":
    main()
