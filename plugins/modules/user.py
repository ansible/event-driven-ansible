#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
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
        - This parameter is valid for AAP 2.5 and onwards.
      default: false
      type: bool
    roles:
      description:
        - Set of roles to be associated with the user.
        - This parameter is only valid and required if targeted controller is AAP 2.4 and O(state=present).
          For AAP 2.5 and onwards this parameter is ignored.
      choices: ["Admin", "Editor", "Contributor", "Operator", "Auditor", "Viewer"]
      type: list
      elements: str
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: Create EDA user
  ansible.eda.user:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    username: "test_collection_user"
    first_name: "Test Collection User"
    last_name: "Test Collection User"
    email: "test@test.com"
    password: "test"
    is_superuser: true
    state: present
  no_log: true

- name: Delete user
  ansible.eda.user:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
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
        username=dict(required=True),
        new_username=dict(),
        first_name=dict(),
        last_name=dict(),
        email=dict(),
        password=dict(no_log=True),
        is_superuser=dict(type="bool", default=False),
        update_secrets=dict(type="bool", default=True),
        state=dict(choices=["present", "absent"], default="present"),
        roles=dict(
            type="list",
            elements="str",
            choices=[
                "Admin",
                "Editor",
                "Contributor",
                "Operator",
                "Auditor",
                "Viewer",
            ],
        ),
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
    roles = module.params.get("roles")

    # Check for AAP 2.4
    config_endpoint_avail = controller.get_endpoint(
        "config",
    )
    is_aap_24 = config_endpoint_avail.status in (404,)
    if is_aap_24 and state == "present" and roles is None:
        module.fail_json(msg="Parameter roles is required while creating a user.")

    ret = {}

    try:
        user_type = controller.get_exactly_one(user_endpoint, name=username)
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

    role_ids = []
    if is_aap_24 and roles:
        for role in roles:
            role_id = controller.resolve_name_to_id("roles", role)
            role_ids.append(role_id)

    if role_ids:
        user_fields["roles"] = role_ids

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
