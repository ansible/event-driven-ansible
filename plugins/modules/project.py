#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
---
module: project
author:
    - Nikhil Jain (@jainnikhil30)
    - Abhijeet Kasurde (@akasurde)
short_description: Create, update or delete project in EDA Controller
description:
    - This module allows user to create, update or delete project in a EDA controller.
version_added: '2.0.0'
options:
    name:
      description:
        - The name of the project.
      type: str
      required: true
    new_name:
      description:
        - Setting this option will change the existing name.
      type: str
    description:
      description:
        - The description of the project.
      type: str
    url:
      description:
        - The git URL of the project.
      type: str
    credential:
      description:
        - The name of the credential to associate with the project.
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
requirements:
  - The 'requests' Python module must be installed.
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = """
- name: Create EDA Projects
  ansible.eda.project:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Project"
    description: "Example project description"
    url: "https://example.com/project1"
    state: present

- name: Update the name of the project
  ansible.eda.project:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Project"
    new_name: "Latest Example Project"
    description: "Example project description"
    url: "https://example.com/project1"
    state: present

- name: Delete the project
  ansible.eda.project:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Project"
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client


def main():
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(required=False),
        url=dict(),
        credential=dict(required=False),
        state=dict(choices=["present", "absent"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec)

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    get_query = {"name": module.params.get("name")}

    resp = client.get(path="/api/eda/v1/projects/", query=get_query)
    module.exit_json(resp.json)


if __name__ == "__main__":
    main()
