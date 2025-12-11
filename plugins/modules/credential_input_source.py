#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing credential input sources in EDA Controller.

This module provides functionality to create, update, or destroy EDA Controller
credential input sources which allow using external secret management systems.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_input_source
author: "Kaio Oliveira (@kaiokmo)"
version_added: "2.9.0"
short_description: create, update, or destroy EDA Controller credential input sources.
description:
  - Create, update, or destroy EDA Controller credential input sources.
  - Credential input sources allow using external secret management systems to provide
    credential field values dynamically.
options:
  description:
    description:
      - The description to use for the credential input source.
    type: str
  input_field_name:
    description:
      - The input field the credential source will be used for
    required: True
    type: str
  metadata:
    description:
      - A JSON or YAML string with additional configuration for the external credential lookup
      - The structure depends on the credential type of the source credential
      - For HashiCorp Vault, should include keys like 'secret_path' and 'secret_key'
    required: False
    type: dict
  target_credential:
    description:
      - The credential name, ID, or named URL which will have its input defined by this source
    required: true
    type: str
  source_credential:
    description:
      - The credential name, ID, or named URL which is the source of the credential lookup
      - This should be a credential configured for external secret management system access
    required: true
    type: str
  organization_name:
    description:
      - The name of the organization.
    type: str
    aliases:
      - organization
  state:
    description:
      - Desired state of the resource.
      - C(present) - Create the credential input source if it doesn't exist,
        or update it if it does exist and changes are needed.
      - C(absent) - Remove the credential input source if it exists.
      - No action if it doesn't exist.
      - C(exists) - Check if the credential input source exists without making
        any changes. Returns the input source details if found, or a 'not found'
        message if it doesn't exist. This state never modifies anything and
        always returns C(changed=False).
    choices: ["present", "absent", "exists"]
    default: "present"
    type: str

extends_documentation_fragment: ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_input_source) supports AAP 2.5 and onwards.
  - Credential input sources require a source credential configured for
    external secret management.
  - Credential input sources are uniquely identified by the combination of
    C(target_credential), C(source_credential), and C(input_field_name).
  - Unlike other EDA resources, credential input sources do not have a C(name)
    field. They are managed based on their composite identity.
  - The C(exists) state is useful for conditional logic in playbooks, allowing
    one to check for input source existence before creating or configuring
    related resources.
  - Only C(description) and C(metadata) fields can be updated on existing
    credential input sources. Other fields (target_credential, source_credential,
    input_field_name) define the identity and cannot be changed.
  - Supported external secret management systems include
    - CyberArk Central Credential Provider Lookup
    - AWS Secrets Manager lookup
    - Microsoft Azure Key Vault
    - Centrify Vault Credential Provider Lookup
    - CyberArk Conjur Secrets Manager Lookup
    - HashiCorp Vault Secret Lookup
    - HashiCorp Vault Signed SSH
    - Thycotic DevOps Secrets Vault
    - Thycotic Secret Server
    - GitHub App Installation Access Token Lookup
  - The metadata structure depends on the credential type of the source credential.
"""


EXAMPLES = r"""
- name: Use CyberArk Lookup credential as password source
  ansible.eda.credential_input_source:
    input_field_name: password
    target_credential: new_cred
    source_credential: cyberark_lookup
    metadata:
      object_query: "Safe=MY_SAFE;Object=awxuser"
      object_query_format: "Exact"
    state: present

- name: Use HashiCorp Vault credential as password source
  ansible.eda.credential_input_source:
    input_field_name: password
    target_credential: my_target_credential
    source_credential: vault_lookup_credential
    metadata:
      secret_path: "secret/myapp"
      secret_key: "password"
    state: present

- name: Remove a credential input source
  ansible.eda.credential_input_source:
    input_field_name: password
    target_credential: my_target_credential
    source_credential: vault_lookup_credential
    state: absent

- name: Check if a credential input source exists
  ansible.eda.credential_input_source:
    input_field_name: password
    target_credential: my_target_credential
    source_credential: vault_lookup_credential
    state: exists
  register: input_source_check

- name: Create input source only if it doesn't exist
  ansible.eda.credential_input_source:
    input_field_name: password
    target_credential: my_target_credential
    source_credential: vault_lookup_credential
    metadata:
      secret_path: "secret/myapp"
      secret_key: "password"
    state: present
  when: input_source_check.msg is defined  # Only if not found

- name: Display input source details if it exists
  debug:
    msg: "Input source ID: {{ input_source_check.id }}"
  when: input_source_check.id is defined  # Only if found
"""


RETURN = r"""
id:
  description: ID of the credential input source.
  returned: when state is 'present' or 'absent' and successful, or when state is 'exists' and the input source is found
  type: int
  sample: 123
changed:
  description: Whether the resource was changed.
  returned: always
  type: bool
  sample: true
msg:
  description: Message describing the result.
  returned: when state is 'exists' and the input source is not found
  type: str
  sample: "Credential input source not found"
input_field_name:
  description: The input field name of the credential input source.
  returned: when state is 'exists' and the input source is found
  type: str
  sample: "password"
target_credential:
  description: The target credential ID.
  returned: when state is 'exists' and the input source is found
  type: int
  sample: 15
source_credential:
  description: The source credential ID.
  returned: when state is 'exists' and the input source is found
  type: int
  sample: 23
metadata:
  description: Metadata configuration for the credential input source.
  returned: when state is 'exists' and the input source is found
  type: dict
  sample: {
    "secret_path": "secret/myapp",
    "secret_key": "password"
  }
description:
  description: Description of the credential input source.
  returned: when state is 'exists' and the input source is found
  type: str
  sample: "Password input source for application"
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    """Main entry point for the credential_input_source module.

    Manages credential input sources in EDA controller by creating, updating,
    or removing them based on the provided parameters and desired state.

    :raises: AnsibleModule.fail_json on errors during input source operations
    :returns: None
    :rtype: None
    """
    argument_spec = dict(
        description=dict(),
        input_field_name=dict(required=True),
        target_credential=dict(required=True),
        source_credential=dict(required=True),
        metadata=dict(type="dict"),
        organization_name=dict(type="str", aliases=["organization"]),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
        token=module.params.get("controller_token"),
    )

    controller = Controller(client, module)

    target_credential = module.params.get("target_credential")
    source_credential = module.params.get("source_credential")
    input_field_name = module.params.get("input_field_name")
    description = module.params.get("description", "")
    metadata = module.params.get("metadata", {})
    organization_name = module.params.get("organization_name")
    state = module.params.get("state")

    try:
        organization_id = None
        if organization_name:
            organization_id = lookup_resource_id(
                module, controller, "organizations", organization_name
            )

        target_credential_id = lookup_resource_id(
            module, controller, "eda-credentials", target_credential
        )
        if not target_credential_id:
            module.fail_json(msg=f"Target credential '{target_credential}' not found")

        source_credential_id = lookup_resource_id(
            module, controller, "eda-credentials", source_credential
        )
        if not source_credential_id:
            if state == "absent":
                module.exit_json(changed=False)
            else:
                module.fail_json(
                    msg=f"Source credential '{source_credential}' not found"
                )

        if state == "present":
            existing_input_source = None
            existing_input_sources = controller.get_endpoint(
                f"eda-credentials/{target_credential_id}/input_sources/"
            )

            if existing_input_sources.status == 200:
                json_data = existing_input_sources.json
                if isinstance(json_data, dict):
                    for source in json_data.get("results", []):
                        source_cred = source.get("source_credential", {})
                        source_cred_id = (
                            source_cred.get("id")
                            if isinstance(source_cred, dict)
                            else source_cred
                        )
                        if (
                            source_cred_id == source_credential_id
                            and source.get("input_field_name") == input_field_name
                        ):
                            existing_input_source = source
                            break

            new_input_source = {
                "target_credential": target_credential_id,
                "source_credential": source_credential_id,
                "input_field_name": input_field_name,
                "description": description,
                "metadata": metadata,
                "organization_id": organization_id,
            }

            if existing_input_source:
                existing_id = existing_input_source["id"]
                needs_update = False

                for field in ["description", "metadata"]:
                    if new_input_source.get(field) != existing_input_source.get(field):
                        needs_update = True

                if needs_update:
                    if module.check_mode:
                        module.exit_json(changed=True, id=existing_id)

                    update_response = controller.patch_endpoint(
                        f"credential-input-sources/{existing_id}/",
                        data=new_input_source,
                    )

                    if update_response.status == 200:
                        module.exit_json(changed=True, id=existing_id)
                    else:
                        module.fail_json(
                            msg=f"Failed to update credential input source: "
                            f"{update_response.status} {update_response.data}"
                        )
                else:
                    module.exit_json(changed=False, id=existing_id)
            else:
                if module.check_mode:
                    module.exit_json(changed=True)

                create_response = controller.post_endpoint(
                    "credential-input-sources/", data=new_input_source
                )

                if create_response.status in [200, 201]:
                    module.exit_json(changed=True, id=create_response.json["id"])
                else:
                    module.fail_json(
                        msg=f"Failed to create credential input source: {create_response.status} {create_response.data}"
                    )
        elif state == "absent":
            existing_input_source = None
            existing_input_sources = controller.get_endpoint(
                f"eda-credentials/{target_credential_id}/input_sources/"
            )

            if existing_input_sources.status == 200:
                json_data = existing_input_sources.json
                if isinstance(json_data, dict):
                    for source in json_data.get("results", []):
                        source_cred = source.get("source_credential", {})
                        source_cred_id = (
                            source_cred.get("id")
                            if isinstance(source_cred, dict)
                            else source_cred
                        )
                        if (
                            source_cred_id == source_credential_id
                            and source.get("input_field_name") == input_field_name
                        ):
                            existing_input_source = source
                            break
            if existing_input_source:
                existing_id = existing_input_source["id"]

                if module.check_mode:
                    module.exit_json(changed=True, id=existing_id)

                delete_response = controller.delete_endpoint(
                    f"credential-input-sources/{existing_id}/"
                )

                if delete_response.status in [202, 204]:
                    module.exit_json(changed=True, id=existing_id)
                else:
                    module.fail_json(
                        msg=f"Failed to delete credential input source: {delete_response.status} {delete_response.data}"
                    )
            else:
                module.exit_json(changed=False)
        elif state == "exists":
            existing_input_source = None
            existing_input_sources = controller.get_endpoint(
                f"eda-credentials/{target_credential_id}/input_sources/"
            )

            if existing_input_sources.status == 200:
                json_data = existing_input_sources.json
                if isinstance(json_data, dict):
                    for source in json_data.get("results", []):
                        source_cred = source.get("source_credential", {})
                        source_cred_id = (
                            source_cred.get("id")
                            if isinstance(source_cred, dict)
                            else source_cred
                        )
                        if (
                            source_cred_id == source_credential_id
                            and source.get("input_field_name") == input_field_name
                        ):
                            existing_input_source = source
                            break

            if existing_input_source:
                module.exit_json(
                    changed=False,
                    id=existing_input_source.get("id"),
                    **existing_input_source,
                )
            else:
                module.exit_json(changed=False, msg="Credential input source not found")

    except EDAError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
