#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: decision_environment
author:
    - Nikhil Jain (@jainnikhil30)
    - Abhijeet Kasurde (@akasurde)
short_description: Create, update or delete decision environment in EDA Controller
description:
    - This module allows user to create, update or delete decision environment in a EDA controller.
version_added: '2.0.0'
options:
    name:
      description:
        - The name of the decision environment.
      type: str
      required: true
    new_name:
      description:
        - Setting this option will change the existing name.
      type: str
    description:
      description:
        - The description of the decision environment.
      type: str
    image_url:
      description:
        - Image URL of the decision environment.
      type: str
    credential:
      description:
        - Name of the credential to associate with the decision environment.
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = """
- name: Create EDA Decision Environment
  ansible.eda.decision_environment:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Decision Environment"
    description: "Example Decision Environment description"
    image_url: "quay.io/test"
    credential: "Example Credential"
    state: present

- name: Update the name of the Decision Environment
  ansible.eda.decision_environment:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Decision Environment"
    new_name: "Latest Example Decision Environment"
    state: present

- name: Delete the the Decision Environment
  ansible.eda.decision_environment:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Decision Environment"
    state: absent
"""

RETURN = """
id:
  description: ID of the decision environment
  returned: when exists
  type: int
  sample: 37
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main():
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        image_url=dict(),
        credential=dict(),
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

    decision_environment_endpoint = "decision-environments"
    controller = Controller(client, module)

    decision_environment_name = module.params.get("name")
    new_name = module.params.get("new_name")
    description = module.params.get("description")
    image_url = module.params.get("image_url")
    state = module.params.get("state")
    credential = module.params.get("credential")
    ret = {}

    try:
        decision_environment_type = controller.get_one_or_many(
            decision_environment_endpoint, name=decision_environment_name
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            ret = controller.delete_if_needed(
                decision_environment_type, endpoint=decision_environment_endpoint
            )
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))
        module.exit_json(**ret)

    decision_environment_type_params = {}
    if description:
        decision_environment_type_params["description"] = description
    if image_url:
        decision_environment_type_params["image_url"] = image_url

    credential_type = None
    if credential:
        try:
            credential_type = controller.get_one_or_many(
                "eda-credentials", name=credential
            )
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))

    if credential_type is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        decision_environment_type_params["credential"] = credential_type["id"]

    if new_name:
        decision_environment_type_params["name"] = new_name
    elif decision_environment_type:
        decision_environment_type_params["name"] = controller.get_item_name(
            decision_environment_type
        )
    else:
        decision_environment_type_params["name"] = decision_environment_name

    # If the state was present and we can let the module build or update
    # the existing decision environment type,
    # this will return on its own
    try:
        ret = controller.create_or_update_if_needed(
            decision_environment_type,
            decision_environment_type_params,
            endpoint=decision_environment_endpoint,
            item_type="decision environment type",
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    module.exit_json(**ret)


if __name__ == "__main__":
    main()
