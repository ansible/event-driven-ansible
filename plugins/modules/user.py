#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: user
author:
    - Nikhil Jain (@jainnikhil30)
    - Abhijeet Kasurde (@akasurde)
short_description: Manage users in EDA controller
description:
    - This module allows the user to create, update or delete users in a EDA controller.
version_added: '2.0.0'
options:
    username:
      description:
        - The name of the user.
        - 150 characters or fewer.
        - Name can contain letters, digits and ('@', '.', '+', '-', '_') only.
      type: str
      required: true
    new_username:
      description:
        - Setting this option will change the existing username.
      type: str
    first_name:
      description:
        - First name of the user.
      type: str
    last_name:
      description:
        - Last name of the user.
      type: str
    email:
      description:
        - Email address of the user.
      type: str
    password:
      description:
        - Write-only field used to change the password.
      type: str
    update_secrets:
      description:
        - V(true) will always change password if user specifies password,
          even if API gives $encrypted$ for password.
        - V(false) will only set the password if other values change too.
      type: bool
      default: true
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    is_superuser:
      description:
        - Make user as superuser.
      default: false
      type: bool
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = """
- name: Create EDA user
  ansible.eda.user:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    username: "test_collection_user"
    first_name: "Test Collection User"
    last_name: "Test Collection User"
    email: "test@test.com"
    password: "test"
    is_superuser: True
    state: present
  no_log: true

- name: Delete user
  ansible.eda.user:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    username: "test_collection_user"
    state: absent

- name: Update the username
  ansible.eda.user:
    username: "test_collection_user"
    new_username: "test_collection_user_updated"
    first_name: "Test Collection User"
    last_name: "Test Collection User"
    email: "test@test.com"
    password: "test"
"""


RETURN = """
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


def main():
    argument_spec = dict(
        username=dict(required=True),
        new_username=dict(),
        first_name=dict(),
        last_name=dict(),
        email=dict(),
        password=dict(no_log=True),
        is_superuser=dict(type="bool", default=False),
        update_secrets=dict(type="bool", default=True),
        state=dict(choices=["present", "absent"], default="present"),
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

    controller = Controller(client, module)
    user_endpoint = "users"

    # Extract the params
    username = module.params.get("username")
    new_username = module.params.get("new_username")
    state = module.params.get("state")
    is_superuser = module.params.get("is_superuser")

    ret = {}

    try:
        user_type = controller.get_one_or_many(user_endpoint, name=username)
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            ret = controller.delete_if_needed(user_type, endpoint=user_endpoint)
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))
        module.exit_json(**ret)

    # User Data that will be sent for create/update
    user_fields = {}
    if new_username:
        user_fields["username"] = new_username
    elif user_type:
        user_fields["username"] = controller.get_item_name(user_type)
    elif username:
        user_fields["username"] = username

    for field_name in (
        "first_name",
        "last_name",
        "email",
        "password",
    ):
        field_value = module.params.get(field_name)
        if field_value is not None:
            user_fields[field_name] = field_value

    user_fields["is_superuser"] = is_superuser

    try:
        ret = controller.create_or_update_if_needed(
            existing_item=user_type,
            new_item=user_fields,
            endpoint=user_endpoint,
            item_type="user",
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))
    module.exit_json(**ret)


if __name__ == "__main__":
    main()
