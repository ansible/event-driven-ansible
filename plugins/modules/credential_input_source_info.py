#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for listing credential input sources from EDA Controller.

This module provides functionality to retrieve information about credential
input sources from an Event-Driven Ansible controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: credential_input_source_info
author: "Kaio Oliveira (@kaiokmo)"
version_added: "2.9.0"
short_description: list credential input sources from EDA Controller.
description:
  - List credential input sources from EDA Controller.
  - Credential input sources link credential fields to external secret management systems.
options:
  target_credential:
    description:
      - Name of the target credential to filter input sources by
      - If specified, only input sources for this credential will be returned
    required: false
    type: str
  source_credential:
    description:
      - Name of the source credential to filter input sources by
      - If specified, only input sources using this external credential will be returned
    required: false
    type: str
  input_field_name:
    description:
      - Name of the input field to filter by
      - If specified, only input sources for this field will be returned
    required: false
    type: str
  organization_name:
    description:
      - The name of the organization to filter by
    required: false
    type: str
    aliases:
      - organization

extends_documentation_fragment: ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_input_source_info) supports AAP 2.5 and onwards.
  - This module retrieves information about credential input sources configured for external secret management.
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
  - Multiple filters can be used together to narrow down results.
"""


EXAMPLES = r"""
- name: List all credential input sources
  ansible.eda.credential_input_source_info:

- name: List input sources for specific target credential
  ansible.eda.credential_input_source_info:
    target_credential: my_target_credential
    organization_name: Default

- name: List input sources using specific source credential
  ansible.eda.credential_input_source_info:
    source_credential: vault_lookup_credential

- name: List input sources for specific field
  ansible.eda.credential_input_source_info:
    input_field_name: password
"""


RETURN = r"""
credential_input_sources:
  description: List of credential input sources.
  returned: always
  type: list
  elements: dict
  sample: [
    {
      "id": 37,
      "input_field_name": "password",
      "target_credential": 15,
      "source_credential": 23,
      "metadata": {
        "secret_path": "secret/myapp",
        "secret_key": "password"
      }
    }
  ]
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    """Main entry point for the credential_input_source_info module.

    Retrieves and returns information about credential input sources from the
    EDA controller with optional filtering.

    :raises: AnsibleModule.fail_json on errors during retrieval
    :returns: None
    :rtype: None
    """
    argument_spec = dict(
        target_credential=dict(type="str", required=False),
        source_credential=dict(type="str", required=False),
        input_field_name=dict(type="str", required=False),
        organization_name=dict(type="str", required=False, aliases=["organization"]),
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
    organization_name = module.params.get("organization_name")

    try:
        query_params = {}

        if target_credential:
            target_cred_response = controller.get_endpoint(
                "eda-credentials/", name=target_credential
            )
            if target_cred_response.status == 200 and target_cred_response.json.get(
                "results"
            ):
                query_params["target_credential"] = target_cred_response.json[
                    "results"
                ][0]["id"]
            else:
                module.fail_json(
                    msg=f"Target credential '{target_credential}' not found"
                )

        if source_credential:
            source_cred_response = controller.get_endpoint(
                "eda-credentials/", name=source_credential
            )
            if source_cred_response.status == 200 and source_cred_response.json.get(
                "results"
            ):
                query_params["source_credential"] = source_cred_response.json[
                    "results"
                ][0]["id"]
            else:
                module.fail_json(
                    msg=f"Source credential '{source_credential}' not found"
                )

        if input_field_name:
            query_params["input_field_name"] = input_field_name

        if organization_name:
            org_response = controller.get_endpoint(
                "organizations/", name=organization_name
            )
            if org_response.status == 200 and org_response.json.get("results"):
                query_params["organization"] = org_response.json["results"][0]["id"]
            else:
                module.fail_json(msg=f"Organization '{organization_name}' not found")

        response = controller.get_endpoint("credential-input-sources/", **query_params)

        if response.status == 200:
            controller.result["credential_input_sources"] = response.json.get(
                "results", []
            )
        else:
            raise EDAError(
                f"Failed to retrieve credential input sources: {response.data}"
            )

    except EDAError as e:
        module.fail_json(msg=str(e))

    module.exit_json(**controller.result)


if __name__ == "__main__":
    main()
