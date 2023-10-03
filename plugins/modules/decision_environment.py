#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2023, Nikhil Jain <nikjain@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = '''
---
module: decision_environment
author: "Nikhil Jain"
short_description: Create, update or delete decision environment in EDA Controller.
description:
  - This module allows you to create, update or delete decision environment in a EDA controller.
version_added: "2.12"
options:
  name:
    description:
      - Name of the decision environment.
    type: str
    required: true
  description:
    description:
      - Description of the decision environment (optional).
    type: str
    required: false
  image_url:
    description:
      - Image URL of the decision environment.
    type: str
    required: false
  credential:
    description:
      - Name of the credential to associate with the decision environment (optional).
    type: str
    required: false
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent", "exists"]
    type: str
extends_documentation_fragment: ansible.eda.auth
'''

EXAMPLES = '''
- name: Create EDA Decision Env
  ansible.eda.decision_environment:
    name: "Example Decision Environment"
    description: "Example Decision Environment description"
    image_url: "quay.io/test"
    credential: "Example Credential"

- name: Delete EDA Decision Env
  ansible.eda.decision_environment:
    name: "Example Decision Environment"
    description: "Example Decision Environment description"
    image_url: "quay.io/test"
    credential: "Example Credential"
    state: absent
'''

from ..module_utils.eda_controller_api import EDAControllerAPIModule


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(),
        description=dict(type="str", required=False),
        image_url=dict(type="str", required=True),
        credential=dict(required=False),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    # Create the module
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the params
    name = module.params.get("name")
    new_name = module.params.get("new_name")
    image_url = module.params.get("image_url")
    credential = module.params.get("credential")
    state = module.params.get("state")

    crendential_id = None
    if credential:
        crendential_id = module.resolve_name_to_id("credentials", credential)

    # Attempt to find project based on the provided name
    decision_environment = module.get_one(
        "decision-environments", name=name, check_exists=(state == "exists")
    )

    if state == "absent":
        module.delete_if_needed(decision_environment, "decision-environments")

    decision_environment_fields = {
        "name": new_name
        if new_name
        else (
            module.get_item_name(decision_environment) if decision_environment else name
        ),
    }
    for field_name in ("description",):
        field_value = module.params.get(field_name)
        if field_name is not None:
            decision_environment_fields[field_name] = field_value

    if crendential_id is not None:
        decision_environment_fields["credential_id"] = crendential_id

    if image_url is not None:
        decision_environment_fields["image_url"] = image_url

    # If the state was present and we can let the module build or update the existing decision environment, this will return on its own
    module.create_or_update_if_needed(
        decision_environment,
        decision_environment_fields,
        endpoint="decision-environments",
        item_type="decision-environment",
    )
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
