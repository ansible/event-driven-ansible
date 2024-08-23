#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

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
    organization_name:
      description:
        - The name of the organization.
        - AAP 2.4 does not support organization name.
      type: str
      aliases:
        - organization
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
- name: Create EDA Projects
  ansible.eda.project:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Project"
    description: "Example project description"
    url: "https://example.com/project1"
    organization_name: Default
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
    organization_name: Default
    state: present

- name: Delete the project
  ansible.eda.project:
    controller_host: https://my_eda_host/
    controller_username: admin
    controller_password: MySuperSecretPassw0rd
    name: "Example Project"
    state: absent
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        url=dict(),
        credential=dict(),
        organization_name=dict(type="str", aliases=["organization"]),
        state=dict(choices=["present", "absent"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [("state", "present", ("name", "url"))]

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

    project_endpoint = "projects"
    controller = Controller(client, module)
    # Organization is not available in Controller 2.4 API
    config_endpoint_avail = controller.get_endpoint(
        "config",
    )
    state = module.params.get("state")
    organization_name = module.params.get("organization_name")
    if state == "present":
        if config_endpoint_avail.status not in (404,) and organization_name is None:
            module.fail_json(
                msg="Parameter organization_name is required when state is present"
            )

    project_name = module.params.get("name")
    new_name = module.params.get("new_name")
    description = module.params.get("description")
    url = module.params.get("url")
    credential = module.params.get("credential")
    ret = {}

    try:
        project_type = controller.get_exactly_one(project_endpoint, name=project_name)
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            ret = controller.delete_if_needed(project_type, endpoint=project_endpoint)
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))
        module.exit_json(**ret)

    project_type_params: dict[str, Any] = {}
    if description:
        project_type_params["description"] = description
    if url:
        project_type_params["url"] = url

    credential_id = None
    if credential:
        credential_id = lookup_resource_id(
            module, controller, "eda-credentials", name=credential
        )

    if credential_id is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        project_type_params["eda_credential_id"] = credential_id

    organization_id = None

    if config_endpoint_avail.status not in (404,) and organization_name:
        organization_id = lookup_resource_id(
            module, controller, "organizations", organization_name
        )

    if organization_id:
        project_type_params["organization_id"] = organization_id

    if new_name:
        project_type_params["name"] = new_name
    elif project_type:
        project_type_params["name"] = controller.get_item_name(project_type)
    else:
        project_type_params["name"] = project_name

    # If the state was present and we can let the module build or update the existing project type,
    # this will return on its own
    try:
        ret = controller.create_or_update_if_needed(
            project_type,
            project_type_params,
            endpoint=project_endpoint,
            item_type="project type",
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    module.exit_json(**ret)


if __name__ == "__main__":
    main()
