#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: decision_environment_info
author:
    - Abhijeet Kasurde (@akasurde)
short_description: List a decision environment in EDA Controller
description:
    - This module allows user to list a decision environment in a EDA controller.
version_added: '2.0.0'
options:
    name:
      description:
        - The name of the decision environment.
      type: str
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: List all EDA Decision Environments
  ansible.eda.decision_environment_info:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd

- name: List a particular EDA Decision Environments
  ansible.eda.decision_environment_info:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: Example
"""

RETURN = r"""
decision_environments:
  description: List of dict containing information about decision environments
  returned: when exists
  type: list
  sample: [
      {
          "created_at": "2024-08-15T21:12:52.218969Z",
          "description": "Example decision environment description",
          "eda_credential_id": null,
          "id": 35,
          "image_url": "https://quay.io/repository/ansible/eda-server",
          "modified_at": "2024-08-15T21:12:52.218994Z",
          "name": "Example Decision environment",
          "organization_id": 1
      }
  ]
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec: dict[str, Any] = dict(
        name=dict(),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    decision_environment_endpoint = "decision-environments"
    controller = Controller(client, module)

    decision_environment_name = module.params.get("name")

    try:
        ret = controller.get_one_or_many(
            decision_environment_endpoint,
            name=decision_environment_name,
            want_one=False,
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))
        raise  # https://github.com/ansible/ansible/pull/83814

    module.exit_json(decision_environments=ret)


if __name__ == "__main__":
    main()
