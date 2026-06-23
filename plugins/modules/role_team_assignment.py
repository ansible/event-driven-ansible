#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: role_team_assignment
author:
    - Brandon Whittington (@B-Whitt)
short_description: Assign a role to a team in EDA Controller
version_added: "2.13.0"
description:
    - This module allows you to create or remove role-based access assignments
      for teams in EDA Controller.
    - Assignments grant a team permissions defined by a role definition,
      optionally scoped to a specific resource (organization, project, etc.).
    - Assignments are immutable after creation. Delete and re-create to change them.
    - This module is for AAP 2.5 only. For AAP 2.6+, use
      ansible.platform.role_team_assignment.
options:
    role_definition:
        description:
            - The name or numeric ID of the role definition that defines
              the permissions to grant.
        required: true
        type: str
    team:
        description:
            - The name or numeric ID of the team receiving the role.
            - Mutually exclusive with I(team_ansible_id).
        required: false
        type: str
    team_ansible_id:
        description:
            - The Ansible resource UUID of the team.
            - Alternative to I(team).
        required: false
        type: str
    object_id:
        description:
            - The numeric primary key of the resource to scope the assignment to.
            - Omit for assignments that do not require a specific resource
              (this depends on the role definition).
            - Mutually exclusive with I(object_ansible_id).
        required: false
        type: int
    object_ansible_id:
        description:
            - The Ansible resource UUID of the resource to scope the assignment to.
            - Alternative to I(object_id).
        required: false
        type: str
    state:
        description:
            - C(present) creates the assignment if it does not exist (idempotent).
            - C(absent) removes the assignment if it exists (idempotent).
            - C(exists) checks whether the assignment is present and returns
              its details. Never modifies anything.
        choices: ["present", "absent", "exists"]
        default: "present"
        type: str
extends_documentation_fragment: ansible.eda.eda_controller.auths
notes:
    - This module is for AAP 2.5 only. For AAP 2.6+, use
      ansible.platform.role_team_assignment.
    - Assignments are immutable. They cannot be updated, only created or deleted.
    - Global roles (content_type=None) cannot be assigned to teams.
    - Organization Member role cannot be assigned to teams.
    - The role definition determines which resource type the assignment applies to.
      The API validates that the object matches the role's content_type.
"""


EXAMPLES = r"""
- name: Assign Organization Auditor to a team for the Default org
  ansible.eda.role_team_assignment:
    role_definition: "Organization Auditor"
    team: "network-ops"
    object_id: 1
    state: present

- name: Assign a role using object_ansible_id for resource scoping
  ansible.eda.role_team_assignment:
    role_definition: "Organization Auditor"
    team: "network-ops"
    object_ansible_id: "550e8400-e29b-41d4-a716-446655440000"
    state: present

- name: Remove a team role assignment
  ansible.eda.role_team_assignment:
    role_definition: "Organization Auditor"
    team: "network-ops"
    object_id: 1
    state: absent

- name: Check if a team role assignment exists
  ansible.eda.role_team_assignment:
    role_definition: "Organization Auditor"
    team: "network-ops"
    object_id: 1
    state: exists
  register: result

- name: Assign a role using numeric IDs
  ansible.eda.role_team_assignment:
    role_definition: "6"
    team: "1"
    object_id: 1
    state: present

- name: Assign a role using team_ansible_id
  ansible.eda.role_team_assignment:
    role_definition: "Organization Auditor"
    team_ansible_id: "550e8400-e29b-41d4-a716-446655440000"
    object_id: 1
    state: present
"""


RETURN = r"""
id:
    description: ID of the role team assignment.
    returned: when the assignment exists or was created
    type: int
    sample: 42
role_definition:
    description: The role definition ID.
    returned: when state is 'exists' and the assignment is found
    type: int
    sample: 6
team:
    description: The team ID.
    returned: when state is 'exists' and the assignment is found
    type: int
    sample: 1
object_id:
    description: The resource primary key the assignment is scoped to.
    returned: when state is 'exists' and the assignment is found
    type: str
    sample: "1"
content_type:
    description: The content type of the scoped resource.
    returned: when state is 'exists' and the assignment is found
    type: str
    sample: "shared.organization"
object_ansible_id:
    description: The Ansible resource UUID of the scoped resource.
    returned: when state is 'exists' and the assignment is found
    type: str
    sample: null
team_ansible_id:
    description: The Ansible resource UUID of the team.
    returned: when state is 'exists' and the assignment is found
    type: str
    sample: "550e8400-e29b-41d4-a716-446655440000"
msg:
    description: Message describing the result.
    returned: when state is 'exists' and the assignment is not found
    type: str
    sample: "Role team assignment not found"
"""


from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def _resolve_id(
    module: AnsibleModule,
    controller: Controller,
    endpoint: str,
    value: str,
    label: str,
) -> Optional[int]:
    """Resolve a name-or-ID string to an integer ID."""
    try:
        return int(value)
    except (ValueError, TypeError):
        pass

    resource_id = lookup_resource_id(module, controller, endpoint, value)
    if resource_id is None:
        module.fail_json(msg=f"{label} '{value}' not found")
    return resource_id


def _find_existing(
    controller: Controller,
    filter_params: dict[str, Any],
    object_id: Optional[int],
    object_ansible_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Find an existing role_team_assignment matching the filter and object."""
    params = dict(filter_params, page_size=200)
    response = controller.get_endpoint("role_team_assignments", data=params)

    if response.status != 200:
        return None

    json_data = response.json
    if not isinstance(json_data, dict):
        return None

    results: list[dict[str, Any]] = json_data.get("results", [])
    for assignment in results:
        if object_ansible_id is not None:
            if str(assignment.get("object_ansible_id")) == str(object_ansible_id):
                return assignment
            continue

        existing_obj_id = assignment.get("object_id")
        if object_id is None and existing_obj_id is None:
            return assignment
        if object_id is not None and str(existing_obj_id) == str(object_id):
            return assignment

    return None


def main() -> None:
    argument_spec = dict(
        role_definition=dict(required=True, type="str"),
        team=dict(type="str"),
        team_ansible_id=dict(type="str"),
        object_id=dict(type="int"),
        object_ansible_id=dict(type="str"),
        state=dict(choices=["present", "absent", "exists"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ("team", "team_ansible_id"),
            ("object_id", "object_ansible_id"),
        ],
        required_one_of=[
            ("team", "team_ansible_id"),
        ],
        supports_check_mode=True,
    )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
        token=module.params.get("controller_token"),
    )

    controller = Controller(client, module)

    role_definition = module.params.get("role_definition")
    team = module.params.get("team")
    team_ansible_id = module.params.get("team_ansible_id")
    object_id = module.params.get("object_id")
    object_ansible_id = module.params.get("object_ansible_id")
    state = module.params.get("state")

    try:
        role_definition_id = _resolve_id(
            module,
            controller,
            "role_definitions",
            role_definition,
            "Role definition",
        )

        team_id = None
        if team is not None:
            team_id = _resolve_id(
                module,
                controller,
                "teams",
                team,
                "Team",
            )

        filter_params: dict[str, Any] = {"role_definition": role_definition_id}
        if team_id is not None:
            filter_params["team"] = team_id
        elif team_ansible_id is not None:
            filter_params["team_ansible_id"] = team_ansible_id
        if object_ansible_id is not None:
            filter_params["object_ansible_id"] = object_ansible_id

        existing = _find_existing(
            controller,
            filter_params,
            object_id,
            object_ansible_id,
        )

        if state == "present":
            if existing:
                module.exit_json(changed=False, id=existing["id"])
                return

            if module.check_mode:
                module.exit_json(changed=True)
                return

            payload: dict[str, Any] = {"role_definition": role_definition_id}
            if team_id is not None:
                payload["team"] = team_id
            elif team_ansible_id is not None:
                payload["team_ansible_id"] = team_ansible_id
            if object_id is not None:
                payload["object_id"] = object_id
            elif object_ansible_id is not None:
                payload["object_ansible_id"] = object_ansible_id

            response = controller.post_endpoint(
                "role_team_assignments",
                data=payload,
            )

            module.exit_json(changed=True, id=response.json["id"])

        elif state == "absent":
            if not existing:
                module.exit_json(changed=False)
                return

            if module.check_mode:
                module.exit_json(changed=True, id=existing["id"])
                return

            response = controller.delete_endpoint(
                f"role_team_assignments/{existing['id']}/",
            )

            module.exit_json(changed=True, id=existing["id"])

        elif state == "exists":
            if existing:
                details = {k: v for k, v in existing.items() if k != "id"}
                module.exit_json(changed=False, id=existing["id"], **details)
            else:
                module.exit_json(
                    changed=False,
                    msg="Role team assignment not found",
                )

    except EDAError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
