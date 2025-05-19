#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: controller_token
author:
    - Abhijeet Kasurde (@akasurde)
short_description: Manage AWX tokens in EDA controller
description:
    - This module allows the user to manage AWX tokens in a EDA controller.
version_added: '2.0.0'
options:
    name:
      description:
        - The name of the AWX token.
      type: str
      required: true
    description:
      description:
        - The description of the project.
        - Required when O(state=present).
      type: str
    token:
      description:
        - The AWX token value.
        - Required when O(state=present).
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
notes:
    - Controller Token API does not support PATCH method, due to this reason the module deletes
      and re-creates the token when existing controller token is found.
      This will cause module to report changed, every time update is called.
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: Create AWX token
  ansible.eda.controller_token:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: "Example AWX token"
    description: "Example AWX token description"
    token: "<TOKEN_VALUE>"
    state: present
  no_log: true

- name: Delete AWX token
  ansible.eda.controller_token:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: "Example AWX token"
    state: absent
"""


RETURN = r"""
id:
    description: ID of the managed AWX token.
    returned: when state is 'present' and successful
    type: str
    sample: "123"
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        token=dict(no_log=True),
        state=dict(choices=["present", "absent"], default="present"),
    )

    required_if = [("state", "present", ("name", "token"))]

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(
        argument_spec=argument_spec, required_if=required_if, supports_check_mode=True
    )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    token_endpoint = "/users/me/awx-tokens/"
    controller = Controller(client, module)

    token_name = module.params.get("name")
    description = module.params.get("description")
    state = module.params.get("state")
    token = module.params.get("token")
    ret = {}

    try:
        token_obj = controller.get_exactly_one(token_endpoint, name=token_name)
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            ret = controller.delete_if_needed(token_obj, endpoint=token_endpoint)
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))
        module.exit_json(**ret)

    # Method 'PATCH' is not allowed, so delete and re-create the token
    if token_obj:
        controller.delete_if_needed(token_obj, endpoint=token_endpoint)

    token_param = {
        "name": token_name,
        "description": description,
        "token": token,
    }
    # Attempt to create the new AWX token
    ret = controller.create_if_needed(
        new_item=token_param,
        endpoint=token_endpoint,
        item_type="controller token",
    )
    module.exit_json(**ret)


if __name__ == "__main__":
    main()
