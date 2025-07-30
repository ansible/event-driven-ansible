#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_input_source
author:
  - "Generated for External SMS integration"
short_description: Manage credential input sources in EDA Controller
description:
    - This module allows the user to create, update or delete a credential input source in EDA controller.
    - Credential input sources allow linking credential fields to external Secret Management Systems (SMS).
version_added: 2.7.0
options:
  target_credential_name:
    description:
      - Name of the target credential that will receive values from the external SMS.
      - This credential should be a regular (non-external) credential.
    type: str
    required: true
  source_credential_name:
    description:
      - Name of the source credential that connects to the external SMS.
      - This credential should be configured for external SMS access (e.g., HashiCorp Vault, Azure Key Vault).
    type: str
    required: true
  input_field_name:
    description:
      - Name of the field in the target credential that will be populated by the external SMS.
    type: str
    required: true
  description:
    description:
      - Description of this credential input source.
    type: str
    default: ""
  metadata:
    description:
      - Metadata configuration for retrieving the secret from the external SMS.
      - The exact format depends on the SMS provider type.
      - For HashiCorp Vault, this might include secret path and key information.
    type: dict
    default: {}
  organization_name:
    description:
      - The name of the organization.
    type: str
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_input_source) supports AAP 2.5 and onwards.
  - Requires the target credential and source credential to exist before creating the input source.
  - The source credential must be configured for external SMS access.
"""


EXAMPLES = r"""
- name: Create a credential input source for HashiCorp Vault
  ansible.eda.credential_input_source:
    target_credential_name: "MyAppCredential"
    source_credential_name: "HashiCorpVaultCred"
    input_field_name: "password"
    description: "Link password field to HashiCorp Vault"
    metadata:
      secret_path: "secret/myapp"
      secret_key: "password"
    organization_name: "Default"
    state: present

- name: Create a credential input source for AWS Secrets Manager
  ansible.eda.credential_input_source:
    target_credential_name: "DatabaseCredential"
    source_credential_name: "AWSSecretsManagerCred"
    input_field_name: "db_password"
    description: "Link database password to AWS Secrets Manager"
    metadata:
      secret_name: "prod/database/credentials"
      secret_key: "password"
    organization_name: "Default"
    state: present

- name: Delete a credential input source
  ansible.eda.credential_input_source:
    target_credential_name: "MyAppCredential"
    source_credential_name: "HashiCorpVaultCred"
    input_field_name: "password"
    organization_name: "Default"
    state: absent
"""


RETURN = r"""
id:
  description: ID of the credential input source.
  returned: on successful create/update
  type: int
  sample: 37
target_credential:
  description: Information about the target credential.
  returned: always
  type: dict
  sample: {
    "id": 15,
    "name": "MyAppCredential"
  }
source_credential:
  description: Information about the source credential.
  returned: always  
  type: dict
  sample: {
    "id": 23,
    "name": "HashiCorpVaultCred"
  }
input_field_name:
  description: Name of the field being populated.
  returned: always
  type: str
  sample: "password"
description:
  description: Description of the credential input source.
  returned: always
  type: str
  sample: "Link password field to HashiCorp Vault"
metadata:
  description: Metadata configuration for the external SMS.
  returned: always
  type: dict
  sample: {
    "secret_path": "secret/myapp",
    "secret_key": "password"
  }
"""

from typing import Any, Dict

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import ControllerArgs
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def create_or_update_credential_input_source(
    controller: Controller, 
    target_credential_id: int,
    source_credential_id: int,
    input_field_name: str,
    description: str,
    metadata: Dict[str, Any],
    organization_id: int,
) -> Dict[str, Any]:
    """Create or update a credential input source."""
    # Check if the input source already exists
    existing_input_sources = controller.get_endpoint(
        f"eda-credentials/{target_credential_id}/input_sources/"
    )
    
    existing_source = None
    if existing_input_sources.status == 200:
        for source in existing_input_sources.json.get("results", []):
            if (source.get("source_credential", {}).get("id") == source_credential_id and
                source.get("input_field_name") == input_field_name):
                existing_source = source
                break
    
    data = {
        "target_credential": target_credential_id,
        "source_credential": source_credential_id,
        "input_field_name": input_field_name,
        "description": description,
        "metadata": metadata,
        "organization": organization_id,
    }
    
    if existing_source:
        # Update existing input source
        response = controller.patch_endpoint(
            f"credential-input-sources/{existing_source['id']}/",
            data=data
        )
        if response.status == 200:
            controller.result["changed"] = True
            return response.json
    else:
        # Create new input source
        response = controller.post_endpoint(
            "credential-input-sources/",
            data=data
        )
        if response.status in (200, 201):
            controller.result["changed"] = True
            return response.json
    
    raise EDAError(f"Failed to create/update credential input source: {response.text}")


def delete_credential_input_source(
    controller: Controller,
    target_credential_id: int,
    source_credential_id: int,
    input_field_name: str,
) -> None:
    """Delete a credential input source."""
    # Find the input source to delete
    existing_input_sources = controller.get_endpoint(
        f"eda-credentials/{target_credential_id}/input_sources/"
    )
    
    if existing_input_sources.status == 200:
        for source in existing_input_sources.json.get("results", []):
            if (source.get("source_credential", {}).get("id") == source_credential_id and
                source.get("input_field_name") == input_field_name):
                # Delete the input source
                response = controller.delete_endpoint(
                    f"credential-input-sources/{source['id']}/"
                )
                if response.status == 204:
                    controller.result["changed"] = True
                    return
                else:
                    raise EDAError(f"Failed to delete credential input source: {response.text}")
    
    # Input source not found - might already be deleted
    controller.result["changed"] = False


def main() -> None:
    argument_spec = ControllerArgs.common_args()
    argument_spec.update(
        dict(
            target_credential_name=dict(type="str", required=True),
            source_credential_name=dict(type="str", required=True),
            input_field_name=dict(type="str", required=True),
            description=dict(type="str", default=""),
            metadata=dict(type="dict", default={}),
            organization_name=dict(type="str"),
            state=dict(choices=["present", "absent"], default="present"),
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
    description = module.params.get("description", "")
    metadata = module.params.get("metadata", {})
    organization_name = module.params.get("organization_name")
    state = module.params.get("state")

    try:
        # Get organization ID
        organization_id = None
        if organization_name:
            org_response = controller.get_endpoint("organizations/", name=organization_name)
            if org_response.status == 200 and org_response.json.get("results"):
                organization_id = org_response.json["results"][0]["id"]
            else:
                module.fail_json(msg=f"Organization '{organization_name}' not found")

        # Get target credential ID
        target_cred_response = controller.get_endpoint("eda-credentials/", name=target_credential_name)
        if target_cred_response.status != 200 or not target_cred_response.json.get("results"):
            module.fail_json(msg=f"Target credential '{target_credential_name}' not found")
        target_credential_id = target_cred_response.json["results"][0]["id"]

        # Get source credential ID
        source_cred_response = controller.get_endpoint("eda-credentials/", name=source_credential_name)
        if source_cred_response.status != 200 or not source_cred_response.json.get("results"):
            module.fail_json(msg=f"Source credential '{source_credential_name}' not found")
        source_credential_id = source_cred_response.json["results"][0]["id"]

        if state == "present":
            result = create_or_update_credential_input_source(
                controller=controller,
                target_credential_id=target_credential_id,
                source_credential_id=source_credential_id,
                input_field_name=input_field_name,
                description=description,
                metadata=metadata,
                organization_id=organization_id,
            )
            controller.result.update(result)
        elif state == "absent":
            delete_credential_input_source(
                controller=controller,
                target_credential_id=target_credential_id,
                source_credential_id=source_credential_id,
                input_field_name=input_field_name,
            )

    except EDAError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**controller.result)


if __name__ == "__main__":
    main()