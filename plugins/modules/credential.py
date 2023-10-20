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
module: credential
author: "Nikhil Jain (@jainnikhil30)"
short_description: Create, update or delete credential in EDA Controller.
description:
  - This module allows you to create, update or delete credential in a EDA 
  controller.
options:
  name:
    description:
      - Name of the credential.
    type: str
    required: true
  new_name:
    description:
      - Setting this option will change the existing name (looked up via the 
      name field).
    type: str
  description:
    description:
      - Description of the credential.
    type: str
    required: false
  username:
    description:
      - The username associated with the credential.
    type: str
  secret:
    description:
      - The password/token associated with the credential.
    type: str
  credential_type:
    description:
      - The type of the credential.
    type: str
    choices:
      - "GitHub Personal Access Token"
      - "GitLab Personal Access Token"
      - "Container Registry"
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent", "exists"]
    type: str
extends_documentation_fragment: ansible.eda.auth
"""

EXAMPLES = """
- name: Create EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    description: "Example credential description"
    username: "test"
    secret: "test"
    credential_type: "GitLab Personal Access Token"

- name: Delete EDA Credential
  ansible.eda.credential:
    name: "Example Credential"
    state: absent
"""


from ..module_utils.eda_controller_api import EDAControllerAPIModule


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(),
        description=dict(type="str", required=False),
        username=dict(type="str"),
        secret=dict(type="str", no_log=True),
        credential_type=dict(
            type="str",
            choices=[
                "GitHub Personal Access Token",
                "GitLab Personal Access Token",
                "Container Registry",
            ],
        ),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    # Create the module
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the params
    name = module.params.get("name")
    new_name = module.params.get("new_name")
    username = module.params.get("username")
    secret = module.params.get("secret")
    credential_type = module.params.get("credential_type")
    state = module.params.get("state")

    # Attempt to find credential based on the provided name
    credential = module.get_one(
        "credentials", name=name, check_exists=(state == "exists")
    )

    if state == "absent":
        module.delete_if_needed(credential, endpoint="credentials")

    # Project Data that will be sent for create/update
    credential_fields = {
        "name": new_name
        if new_name
        else (module.get_item_name(credential) if credential else name),
    }
    for field_name in "description":
        field_value = module.params.get(field_name)
        if field_name is not None:
            credential_fields[field_name] = field_value

    if username is not None:
        credential_fields["username"] = username

    if secret is not None:
        credential_fields["secret"] = secret

    if credential_type is not None:
        credential_fields["credential_type"] = credential_type

    # If the state was present and we can let the module build or update the
    # existing credential, this will return on its own
    module.create_or_update_if_needed(
        credential,
        credential_fields,
        endpoint="credentials",
        item_type="credential",
    )
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
