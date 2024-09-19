#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: rulebook_info
author:
  - Alina Buzachis (@alinabuzachis)
short_description: List all rulebooks
description:
    - List all rulebooks.
version_added: 2.1.0
options:
  name:
    description:
      - The name of the rulebook.
      - If only O(name) is set, all rulebooks with the specific name will be listed in different projects.
        For a granular filtering, use O(name) in combination with O(project).
    type: str
    required: false
  project_name:
    description:
      - The name of the project.
    type: str
    required: false
    aliases:
      - project
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
"""


EXAMPLES = """
- name: Get information about a rulebook
  ansible.eda.rulebook_info:
    name: "Example Rulebook Activation"
    project_name: "Example Project"

- name: List all rulebooks
  ansible.eda.rulebook_info:
"""


RETURN = """
rulebooks:
  description: Information about rulebooks.
  returned: always
  type: list
  elements: dict
  sample: [
    {
      "created_at": "2024-09-13T16:13:28.268659Z",
      "description": "",
      "id": 893,
      "modified_at": "2024-09-13T16:13:28.268712Z",
      "name": "demo_controller_rulebook.yml",
      "organization_id": 1,
      "project_id": 177,
      "rulesets": "",
      "sources": [
        {
          "name": "__SOURCE_1",
          "rulebook_hash": "1e0f22025ab0a4e729fb68bcb9497412c3d9f477ce5a8cb91cc2ef15e35c4dc6",
          "source_info": "ansible.eda.range:\n  limit: 5\n"
        }
      ]
    }
]

"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=False),
        project_name=dict(type="str", required=False, aliases=["project"]),
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

    params = {}
    result = []
    name = module.params.get("name")

    controller = Controller(client, module)

    # Get the project id
    project_id = None
    if module.params.get("project_name"):
        project_id = lookup_resource_id(
            module, controller, "projects", module.params["project_name"]
        )
    if project_id is not None:
        params = {"data": {"project_id": project_id}}

    # Attempt to look up rulebook
    try:
        rulebooks = controller.get_one_or_many("rulebooks", name=name, **params)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook: {e}")

    if len(rulebooks) > 0:
        for rulebook in rulebooks:
            item = rulebook.copy()
            try:
                sources = controller.get_one_or_many(
                    f"rulebooks/{item['id']}/sources", name=item["name"]
                )
                item["sources"] = sources
            except EDAError as e:
                module.fail_json(msg=f"Failed to get rulebook source list: {e}")
            result.append(item)

    module.exit_json(rulebooks=result)


if __name__ == "__main__":
    main()
