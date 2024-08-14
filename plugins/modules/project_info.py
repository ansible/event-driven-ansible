#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: project_info
author:
    - Abhijeet Kasurde (@akasurde)
short_description: List projects in EDA Controller
description:
    - This module allows user to list project in a EDA controller.
version_added: '2.0.0'
options:
    name:
      description:
        - The name of the project.
        - Return information about particular project available on EDA Controller.
      type: str
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = """
- name: List a particular project
  ansible.eda.project_info:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example"
    register: r

- name: List all projects
  ansible.eda.project_info:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    register: r
"""

RETURN = """
projects:
  description: List of dicts containing information about projects
  returned: success
  type: list
  sample: [
      {
          "created_at": "2024-08-12T20:35:28.367702Z",
          "description": "",
          "eda_credential_id": null,
          "git_hash": "417b4dbe9b3472fd64212ef8233b865585e5ade3",
          "id": 17,
          "import_error": null,
          "import_state": "completed",
          "modified_at": "2024-08-12T20:35:28.367724Z",
          "name": "Sample Example Project",
          "organization_id": 1,
          "proxy": "",
          "scm_branch": "",
          "scm_refspec": "",
          "scm_type": "git",
          "signature_validation_credential_id": null,
          "url": "https://github.com/ansible/ansible-ui",
          "verify_ssl": true
      },
  ]
"""  # NOQA

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.eda.plugins.module_utils.arguments import AUTH_ARGSPEC
from ansible_collections.ansible.eda.plugins.module_utils.client import Client
from ansible_collections.ansible.eda.plugins.module_utils.controller import Controller
from ansible_collections.ansible.eda.plugins.module_utils.errors import EDAError


def main():
    argument_spec = dict(
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

    project_endpoint = "projects"
    controller = Controller(client, module)

    project_name = module.params.get("name")

    ret = {}

    try:
        ret = controller.get_one_or_many(
            project_endpoint, name=project_name, want_one=False
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if ret is None:
        ret = []
    if not isinstance(ret, list):
        ret = [ret]
    module.exit_json(projects=ret)


if __name__ == "__main__":
    main()
