#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
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
    proxy:
      description:
        - Proxy used to access HTTP or HTTPS servers.
      type: str
      version_added: '2.7.0'
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
    scm_branch:
      description:
        - The scm branch of the git project.
      type: str
      version_added: 2.8.0
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    sync:
      description:
        - Triggers the synchronization of the project.
        - This only takes effect when the project already exists.
      type: bool
      default: False
      version_added: 2.2.0
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: Create EDA Projects
  ansible.eda.project:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: "Example Project"
    description: "Example project description"
    url: "https://example.com/project1"
    proxy: "https://example.com"
    organization_name: Default
    state: present

- name: Update the name of the project
  ansible.eda.project:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: "Example Project"
    new_name: "Latest Example Project"
    description: "Example project description"
    url: "https://example.com/project1"
    scm_branch: "devel"
    organization_name: Default
    state: present

- name: Delete the project
  ansible.eda.project:
    aap_hostname: https://my_eda_host/
    aap_username: admin
    aap_password: MySuperSecretPassw0rd
    name: "Example Project"
    state: absent
"""

RETURN = r"""
id:
  description: ID of the project.
  returned: when exists
  type: int
  sample: 24
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
        proxy=dict(),
        credential=dict(),
        scm_branch=dict(),
        organization_name=dict(type="str", aliases=["organization"]),
        state=dict(choices=["present", "absent"], default="present"),
        sync=dict(type="bool", default=False),
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

    project_endpoint = "projects"
    controller = Controller(client, module)
    # Organization is not available in Controller 2.4 API
    config_endpoint_avail = controller.get_endpoint(
        "config",
    )
    state = module.params.get("state")
    organization_name = module.params.get("organization_name")
    project_name = module.params.get("name")
    url = module.params.get("url")
    proxy = module.params.get("proxy")
    sync_enabled = module.params.get("sync")
    project = {}

    try:
        project = controller.get_exactly_one(project_endpoint, name=project_name)
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == "present":
        if not project and not url:
            module.fail_json(
                msg="Parameter url is required when state is present and project does not exist"
            )
        if (
            config_endpoint_avail.status not in (404,)
            and organization_name is None
            and not project
        ):
            module.fail_json(
                msg="Parameter organization_name is required when state is present and project does not exist"
            )

    new_name = module.params.get("new_name")
    description = module.params.get("description")
    scm_branch = module.params.get("scm_branch")
    credential = module.params.get("credential")
    ret = {}

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            ret = controller.delete_if_needed(project, endpoint=project_endpoint)
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))
        module.exit_json(**ret)

    project_params: dict[str, Any] = {}
    if description:
        project_params["description"] = description
    if url:
        project_params["url"] = url
    if scm_branch:
        project_params["scm_branch"] = scm_branch
    if proxy:
        project_params["proxy"] = proxy

    credential_id = None
    if credential:
        credential_id = lookup_resource_id(
            module, controller, "eda-credentials", name=credential
        )

    if credential_id is not None:
        # this is resolved earlier, so save an API call and don't do it again
        # in the loop above
        project_params["eda_credential_id"] = credential_id

    organization_id = None

    if config_endpoint_avail.status not in (404,) and organization_name:
        organization_id = lookup_resource_id(
            module, controller, "organizations", organization_name
        )

    if organization_id:
        project_params["organization_id"] = organization_id

    if new_name:
        project_params["name"] = new_name
    elif project:
        project_params["name"] = controller.get_item_name(project)
    else:
        project_params["name"] = project_name

    # If the state was present and we can let the module build or update the existing project,
    # this will return on its own
    try:
        ret = controller.create_or_update_if_needed(
            project,
            project_params,
            endpoint=project_endpoint,
            item_type="project",
        )
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if sync_enabled and project:
        sync_endpoint = f"{project_endpoint}/{ret['id']}/sync"
        try:
            controller.create(
                {"name": project_params["name"]},
                endpoint=sync_endpoint,
                item_type="sync",
            )
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))

    module.exit_json(**ret)


if __name__ == "__main__":
    main()
