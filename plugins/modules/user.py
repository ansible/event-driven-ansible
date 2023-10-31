#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2023, Nikhil Jain <nikjain@redhat.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: user
author: "Nikhil Jain (@jainnikhil30)"
short_description: Create, update or delete project in EDA Controller.
description:
  - This module allows you to create, update or delete project in a EDA
    controller.
options:
  username:
    description:
      - Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
    required: True
    type: str
  new_username:
    description:
      - Setting this option will change the existing username (looked up via
        the name field.
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
  roles:
    description:
      - Set of roles to be associated with the user
    choices: ["Admin", "Editor", "Contributor", "Operator", "Auditor", "Viewer"]
    type: list
    elements: str
  update_secrets:
    description:
      - C(true) will always change password if user specifies password,
        even if API gives $encrypted$ for password.
      - C(false) will only set the password if other values change too.
    type: bool
    default: true
  state:
    description:
      - Desired state of the resource.
    choices: ["present", "absent", "exists"]
    default: "present"
    type: str
extends_documentation_fragment: ansible.eda.auth
"""

EXAMPLES = """
- name: Create EDA User
  ansible.eda.user:
    username: "test_collection_user"
    first_name: "Test Collection User"
    last_name: "Test Collection User"
    email: "test@test.com"
    password: "test"
    roles: ["Admin"]

- name: Delete EDA User
  ansible.eda.user:
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
    roles: ["Admin"]
"""

from ..module_utils.eda_controller_api import EDAControllerAPIModule


def main():
    argument_spec = dict(
        username=dict(required=True),
        new_username=dict(),
        first_name=dict(),
        last_name=dict(),
        email=dict(),
        password=dict(no_log=True),
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
        update_secrets=dict(type="bool", default=True, no_log=False),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    # Create the module
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the params
    username = module.params.get("username")
    new_username = module.params.get("new_username")
    roles = module.params.get("roles")
    state = module.params.get("state")

    # Attempt to find user based on the provided name
    user = module.get_one("users", name=username, check_exists=(state == "exists"))

    if state == "absent":
        module.delete_if_needed(user, endpoint="users")

    role_id = []
    if roles:
        for role in roles:
            id = module.resolve_name_to_id("roles", role)
            role_id.append(id)

    # User Data that will be sent for create/update
    user_fields = {
        "username": new_username
        if new_username
        else (module.get_item_name(user) if user else username),
    }
    for field_name in (
        "first_name",
        "last_name",
        "email",
        "password",
    ):
        field_value = module.params.get(field_name)
        if field_name is not None:
            user_fields[field_name] = field_value

    if len(role_id) != 0:
        user_fields["roles"] = role_id

    # If the state was present and we can let the module build or update the
    # existing user, this will return on its own
    module.create_or_update_if_needed(
        user,
        user_fields,
        endpoint="users",
        item_type="user",
    )
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
