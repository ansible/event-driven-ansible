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
module: activation
author: "Nikhil Jain (@jainnikhil30)"
short_description: Create and delete rulebook activations in EDA Controller.
description:
  - This module allows you to create, restart or delete activations in a EDA.
options:
  name:
    description:
      - The name of the rulebook activation.
    type: str
    required: true
  description:
    description:
      - The description of the rulebook activation (optional).
    type: str
    required: false
  project:
    description:
      - The name of the project associated with the rulebook activation.
    type: str
  rulebook:
    description:
      - The name of the rulebook associated with the rulebook activation.
    type: str
  extra_vars:
    description:
      - The extra variables for the rulebook activation, default is ''.
    type: str
    default: ''
  restart_policy:
    description:
      - The restart policy for the rulebook activation, default is 'on-failure'.
    default: 'on-failure'
    choices: ["on-failure", "always", "never"]
    type: str
  enabled:
    description:
      - Whether the rulebook activation is enabled or not, default 'True'.
    type: bool
    default: true
  decision_environment:
    description:
      - The name of the decision environment associated with the activation.
    type: str
  awx_token_id:
    description:
      - The controller token ID is required 
    type: int 
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent", "exists"]
    type: str
extends_documentation_fragment: ansible.eda.auth
"""

EXAMPLES = """
- name: Create EDA Activation
  ansible.eda.activation:
    name: "Example Activation"
    description: "Example Activation description"
    project: "Example Project"
    rulebook: "hello_controller.yml"
    decision_environment: "Default Decision Environment"
    enabled: False
    awx_token_id: 1

- name: Delete EDA Activation
  ansible.eda.activation:
    name: "Example Activation"
    state: absent
"""


from ..module_utils.eda_controller_api import EDAControllerAPIModule


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        description=dict(required=False),
        project=dict(type="str"),
        rulebook=dict(type="str"),
        extra_vars=dict(type="str", default=""),
        restart_policy=dict(
            type="str",
            default="on-failure",
            choices=[
                "on-failure",
                "always",
                "never",
            ],
        ),
        enabled=dict(type="bool", default=True),
        decision_environment=dict(type="str"),
        awx_token_id=dict(type="int"),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    # Create the module
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the params
    name = module.params.get("name")
    project = module.params.get("project")
    rulebook = module.params.get("rulebook")
    restart_policy = module.params.get("restart_policy")
    enabled = module.params.get("enabled")
    decision_environment = module.params.get("decision_environment")
    state = module.params.get("state")
    awx_token_id = module.params.get("awx_token_id")

    # get the project id
    project_id = None
    if project:
        project_id = module.resolve_name_to_id("projects", project)

    # get the rulebook id
    rulebook_id = None
    if rulebook:
        rulebook_id = module.resolve_name_to_id("rulebooks", rulebook)

    # get the decision environment id
    decision_environment_id = None
    if decision_environment:
        decision_environment_id = module.resolve_name_to_id(
            "decision-environments", decision_environment
        )

    # Attempt to find rulebook activation based on the provided name
    activation = module.get_one(
        "activations", name=name, check_exists=(state == "exists")
    )

    if state == "absent":
        module.delete_if_needed(activation, endpoint="activations")

    # Activation Data that will be sent for create/update
    activation_fields = {
        "name": module.get_item_name(activation) if activation else name,
    }
    for field_name in (
        "description",
        "extra_vars",
    ):
        field_value = module.params.get(field_name)
        if field_name is not None:
            activation_fields[field_name] = field_value

    if project_id is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        activation_fields["project_id"] = project_id

    if rulebook_id is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        activation_fields["rulebook_id"] = rulebook_id

    if decision_environment_id is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        activation_fields["decision_environment_id"] = decision_environment_id

    if awx_token_id is not None:
        activation_fields["awx_token_id"] = awx_token_id

    if restart_policy is not None:
        activation_fields["restart_policy"] = restart_policy

    if enabled is not None:
        activation_fields["is_enabled"] = enabled

    # If the state was present and we can let the module build or update the
    # existing activation, this will return on its own
    module.create_or_update_if_needed(
        activation,
        activation_fields,
        endpoint="activations",
        item_type="activation",
    )
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
