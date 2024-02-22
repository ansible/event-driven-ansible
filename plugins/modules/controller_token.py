#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2023, Sarath Padakandla <spadakan@redhat.com> GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ..module_utils.eda_controller_api import EDAControllerAPIModule

__metaclass__ = type

ANSIBLE_METADATA = {
    "status": ["preview"],
    "supported_by": "community",
}
DOCUMENTATION = """
---
module: controller_token
short_description: Manage AWX tokens in EDA
version_added: "1.0"
description:
    - "This module manages AWX tokens for a user in the EDA Controller."
options:
    name:
        description:
            - Name of the AWX token.
        required: true
    description:
        description:
            - Description of the AWX token. Required when state is 'present'.
        required: false
    token:
        description:
            - The AWX token value. Required when state is 'present'.
        required: false
    state:
        description:
            - Indicates the desired state of the AWX token.
        default: 'present'
        choices: ['present', 'absent']
requirements:
  - The 'requests' Python module must be installed.
extends_documentation_fragment: ansible.eda.auth
"""

EXAMPLES = """
- name: Create AWX token
  ansible.eda.controller_token:
    name: "foo"
    description: "bar"
    token: "lkajfdlkjds"
    state: present

- name: Delete AWX token
  ansible.eda.controller_token:
    name: "foo"
    state: absent
"""

RETURN = """
id:
    description: ID of the managed AWX token.
    returned: when state is 'present' and successful
    type: str
    sample: "123"
changed:
    description: Indicates if the resource has been created or deleted.
    returned: always
    type: bool
"""


def main():
    # Define the specific arguments for this module
    argument_spec = dict(
        name=dict(type="str", required=True),
        description=dict(type="str", required=False, default=""),
        token=dict(type="str", required=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )

    # Create an instance of the EDAControllerAPIModule with the defined arguments
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the parameters
    name = module.params.get("name")
    description = module.params.get("description")
    token = module.params.get("token")
    state = module.params.get("state")

    if state == "present":
        # Prepare the payload for the new AWX token
        new_item = {
            "name": name,
            "description": description,
            "token": token,
        }

        # Check if a token with the same name already exists
        existing_token = module.get_one("/users/me/awx-tokens/", name=name, allow_none=True)

        # If a token with the same name exists, delete it
        if existing_token:
            module.delete_if_needed(
                existing_item=existing_token,
                endpoint="/users/me/awx-tokens/"
            )

        # Attempt to create the new AWX token
        module.create_if_needed(
            existing_item=None,
            new_item=new_item,
            endpoint="/users/me/awx-tokens/",
            item_type="awx-tokens",
        )
    elif state == "absent":
        # Check if a token with the name exists
        existing_token = module.get_one("/users/me/awx-tokens/", name=name, allow_none=True)

        # If it exists, delete it
        if existing_token:
            module.delete_if_needed(
                existing_item=existing_token,
                endpoint="/users/me/awx-tokens/"
            )
        else:
            module.fail_json(msg="AWX token with name '{}' not found.".format(name))

    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
