#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2023, Nikhil Jain <nikjain@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: project
author: Nikhil Jain
short_description: Create, update or delete project in EDA Controller.
description:
  - This module allows you to create, update or delete project in a EDA controller.
options:
  name:
    description:
      - The name of the project.
    type: str
    required: true
  new_name:
    description:
      - Setting this option will change the existing name (looked up via the name field).
    type: str
  description:
    description:
      - The description of the project (optional).
    type: str
    required: false
  url:
    description:
      - The Git URL of the project.
    type: str
    required: true
  credential:
    description:
      - The name of the credential to associate with the project (optional).
    type: str
    required: false
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent", "exists"]
    type: str
requirements:
  - The 'requests' Python module must be installed.
extends_documentation_fragment: ansible.eda.auth
"""

EXAMPLES = """
- name: Create EDA Projects
  ansible.eda.project:
    name: "Example Project"
    description: "Example project description"
    url: "http://example.com/project1"
    state: present

- name: Update the name of the project
  ansible.eda.project:
    name: "Example Project"
    new_name: "Latest Example Project"
    description: "Example project description"
    url: "http://example.com/project1"
    state: present

- name: Delete the project
  ansible.eda.project:
    name: "Example Project"
    description: "Example project description"
    url: "http://example.com/project1"
    state: absent
"""


from ..module_utils.eda_controller_api import EDAControllerAPIModule


def main():
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(required=False),
        url=dict(required=True),
        credential=dict(required=False),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    # Create the module
    module = EDAControllerAPIModule(argument_spec=argument_spec)

    # Extract the params
    name = module.params.get("name")
    new_name = module.params.get("new_name")
    credential = module.params.get("credential")
    state = module.params.get("state")

    crendential_id = None
    if credential:
        crendential_id = module.resolve_name_to_id("credentials", credential)

    # Attempt to find project based on the provided name
    project = module.get_one("projects", name=name, check_exists=(state == "exists"))

    if state == "absent":
        module.delete_if_needed(project, endpoint="projects")

    # Project Data that will be sent for create/update
    project_fields = {
        "name": new_name
        if new_name
        else (module.get_item_name(project) if project else name),
    }
    for field_name in (
        "description",
        "url",
    ):
        field_value = module.params.get(field_name)
        if field_name is not None:
            project_fields[field_name] = field_value

    if crendential_id is not None:
        # this is resolved earlier, so save an API call and don't do it again in the loop above
        project_fields["credential"] = crendential_id

    # If the state was present and we can let the module build or update the existing project, this will return on its own
    module.create_or_update_if_needed(
        project,
        project_fields,
        endpoint="projects",
        item_type="project",
    )
    module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()
