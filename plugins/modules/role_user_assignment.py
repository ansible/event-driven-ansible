#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: role_user_assignment
author: "Tom Page (@Tompage1994)"
short_description: Gives a user permission to a resource or an organization.
description:
    - Use this endpoint to give a user permission to a resource or an organization.
    - After creation, the assignment cannot be edited, but can be deleted to remove those permissions.
options:
    role_definition:
        description:
            - The name of the role definition to assign to the user.
        required: True
        type: str
    object_id:
        description:
            - Primary key of the object this assignment applies to.
        required: False
        type: int
    user:
        description:
            - The name of the user to assign to the object.
        required: False
        type: str
    object_ansible_id:
        description:
            - Resource id of the object this role applies to. Alternative to the object_id field.
        required: False
        type: str
    user_ansible_id:
        description:
            - Resource id of the user who will receive permissions from this assignment. Alternative to user field.
        required: False
        type: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent", "exists"]
      default: "present"
      type: str
extends_documentation_fragment:
- ansible.platform.auth
'''


EXAMPLES = '''
- name: Give Administrators organization admin role for org 1
  ansible.platform.role_user_assignment:
    role_definition: Organization Admin
    object_id: 1
    user: Administrators
    state: present
...
'''

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError

def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        user=dict(required=False, type='str'),
        object_id=dict(required=False, type='int'),
        role_definition=dict(required=True, type='str'),
        object_ansible_id=dict(required=False, type='str'),
        user_ansible_id=dict(required=False, type='str'),
        state=dict(default='present', choices=['present', 'absent', 'exists']),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('user', 'user_ansible_id'),
            ('object_id', 'object_ansible_id'),
        ],
        required_one_of=[
            ('user', 'user_ansible_id'),
            ('object_id', 'object_ansible_id'),
        ]
    )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    user_param = module.params.get('user')
    object_id = module.params.get('object_id')
    role_definition_str = module.params.get('role_definition')
    object_ansible_id = module.params.get('object_ansible_id')
    user_ansible_id = module.params.get('user_ansible_id')
    state = module.params.get('state')

    controller = Controller(client, module)

    role_definition = controller.get_exactly_one('role_definitions', name=role_definition_str)
    user = controller.get_exactly_one('users', name=user_param)

    new_item = {
        'role_definition': role_definition['id']
    }

    if object_id is not None:
        new_item['object_id'] = object_id
    if user is not None:
        new_item['user'] = user['id'] if user else None
    if object_ansible_id is not None:
        new_item['object_ansible_id'] = object_ansible_id
    if user_ansible_id is not None:
        new_item['user_ansible_id'] = user_ansible_id

    try:
        assignment = controller.get_one_or_many(
                                'role_user_assignments',
                                **{'data': new_item}
                            )
        assignment = assignment[0] if len(assignment) == 1 else None
    except EDAError as eda_err:
        module.fail_json(msg=str(eda_err))

    if state == 'absent':
        try:
            ret = controller.delete_if_needed(
                    assignment,
                    endpoint='role_user_assignments'
                )
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))

    elif state == 'present' and assignment is None:
        try:
            ret = controller.create_if_needed(
                        new_item=new_item,
                        endpoint='role_user_assignments',
                        item_type='role_user_assignment',
                    )
        except EDAError as eda_err:
            module.fail_json(msg=str(eda_err))

    else:
        ret = {'changed': False}

    module.exit_json(**ret)


if __name__ == '__main__':
    main()
