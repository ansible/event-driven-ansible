#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: event_stream
author:
   - Alina Buzachis (@alinabuzachis)
short_description: Manage event streams in EDA Controller
description:
    - This module allows the user to create, update or delete a event streams in EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - Name of the event stream.
    type: str
    required: true
  new_name:
    description:
      - Setting this option will change the existing name (lookup via name).
    type: str
  credential_name:
    description:
      - The name of the credential.
      - The type of credential can only be one of ['HMAC Event Stream',
        'Basic Event Stream', 'Token Event Stream', 'OAuth2 Event Stream',
        'OAuth2 JWT Event Stream', 'ECDSA Event Stream', 'mTLS Event Stream',
        'GitLab Event Stream', 'GitHub Event Stream', 'ServiceNow Event Stream',
        'Dynatrace Event Stream']
    type: str
    aliases:
      - credential
  organization_name:
    description:
      - The name of the organization.
    type: str
    aliases:
      - organization
  event_stream_type:
    description:
      - Type of the event stream.
      - This field is not necessary to create an event stream and will be ignored.
      - This field will be removed in version 3.0.0.
    type: str
    aliases:
      - type
  headers:
    description:
      - Comma separated HTTP header keys that you want to include in the event payload.
        To include all headers in the event payload, leave the field empty.
    type: str
    default: ''
    version_added: 2.1.0
  forward_events:
    description:
      - Enable the event stream to forward events to the rulebook activation where it is configured.
    type: bool
    default: false
    version_added: 2.1.0
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.event_stream) supports AAP 2.5 and onwards.
"""


EXAMPLES = r"""
- name: Create an EDA Event Stream
  ansible.eda.event_stream:
    name: "Example Event Stream"
    credential_name: "Example Credential"
    organization_name: Default

- name: Delete an EDA Event Stream
  ansible.eda.event_stream:
    name: "Example Event Stream"
    state: absent
"""


RETURN = r"""
id:
  description: ID of the event stream.
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


def create_params(module: AnsibleModule, controller: Controller) -> dict[str, Any]:
    credential_params: dict[str, Any] = {}

    if module.params.get("forward_events") is not None:
        if module.params["forward_events"]:
            credential_params["test_mode"] = False
        else:
            credential_params["test_mode"] = True

    if module.params.get("headers"):
        credential_params["additional_data_headers"] = module.params["headers"]

    credential_id = None
    if module.params.get("credential_name"):
        credential_id = lookup_resource_id(
            module,
            controller,
            "eda-credentials",
            module.params["credential_name"],
        )

    if credential_id:
        credential_params["eda_credential_id"] = credential_id

    organization_id = None
    organization_name = module.params.get("organization_name")
    if organization_name:
        organization_id = lookup_resource_id(
            module, controller, "organizations", organization_name
        )

    if organization_id:
        credential_params["organization_id"] = organization_id

    return credential_params


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        credential_name=dict(type="str", aliases=["credential"]),
        organization_name=dict(type="str", aliases=["organization"]),
        headers=dict(type="str", default=""),
        forward_events=dict(type="bool", default=False),
        state=dict(choices=["present", "absent"], default="present"),
        # fix: event_stream_type is not used in the module
        event_stream_type=dict(
            type="str",
            aliases=["type"],
            removed_in_version="3.0.0",
            removed_from_collection="ansible.eda",
        ),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [
        (
            "state",
            "present",
            ("name", "credential_name", "organization_name"),
        )
    ]

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

    controller = Controller(client, module)
    event_stream_endpoint = "event-streams"
    event_stream_path = controller.get_endpoint(event_stream_endpoint)
    if event_stream_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.event_stream supports AAP 2.5 and onwards"
        )

    state = module.params.get("state")
    organization_name = module.params.get("organization_name")

    if state == "present":
        if event_stream_path.status not in (404,) and organization_name is None:
            module.fail_json(
                msg="Parameter organization_name is required when state is present"
            )

    name = module.params.get("name")
    new_name = module.params.get("new_name")

    # Attempt to look up event stream based on the provided name
    event_stream = {}
    try:
        event_stream = controller.get_exactly_one(event_stream_endpoint, name=name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get event stream: {e}")

    if state == "absent":
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        try:
            result = controller.delete_if_needed(
                event_stream, endpoint=event_stream_endpoint
            )
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete event stream: {e}")

    # Activation Data that will be sent for create/update
    event_stream_params = create_params(module, controller)
    event_stream_params["name"] = (
        new_name
        if new_name
        else (controller.get_item_name(event_stream) if event_stream else name)
    )

    # If the state was present and we can let the module build or update the
    # existing event stream, this will return on its own
    try:
        result = controller.create_or_update_if_needed(
            event_stream,
            event_stream_params,
            endpoint=event_stream_endpoint,
            item_type="event stream",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update event stream: {e}")


if __name__ == "__main__":
    main()
