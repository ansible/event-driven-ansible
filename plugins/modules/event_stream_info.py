#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: event_stream_info
author:
  - Alina Buzachis (@alinabuzachis)
short_description: List event streams in the EDA Controller
description:
    - List event streams in the EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - The name of the event stream.
    type: str
    required: false
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.event_stream_info) supports AAP 2.5 and onwards.
"""


EXAMPLES = r"""
  - name: Get information about a event stream
    ansible.eda.event_stream_info:
      name: "Test"

  - name: List all event streams
    ansible.eda.event_stream_info:
"""


RETURN = r"""
event_streams:
  description: Information about event streams.
  returned: always
  type: list
  elements: dict
  sample:  [
    {
      "additional_data_headers": "",
      "created_at": "2024-08-30T11:19:49.064112Z",
      "eda_credential": {
          "credential_type_id": 218,
          "description": "This is a test credential",
          "id": 200,
          "inputs": {
              "auth_type": "basic",
              "http_header_key": "Authorization",
              "password": "$encrypted$",
              "username": "test"
          },
          "managed": false,
          "name": "Test_Credential_3db838f4-299c-51bf-8ff5-47f6d24fc5a7",
          "organization_id": 1
      },
      "event_stream_type": "hmac",
      "events_received": 0,
      "id": 4,
      "last_event_received_at": null,
      "modified_at": "2024-08-30T11:19:51.825860Z",
      "name": "Test_EvenStream_3db838f4-299c-51bf-8ff5-47f6d24fc5a7",
      "organization": {
          "description": "The default organization",
          "id": 1,
          "name": "Default"
      },
      "owner": "admin",
      "test_content": "",
      "test_content_type": "",
      "test_error_message": "",
      "test_headers": "",
      "test_mode": false,
      "url": "https://eda-server:8443/edgecafe/api/eda/v1/external_event_stream/18584cf5/post/"
    }
  ]
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=False),
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

    name = module.params.get("name")
    controller = Controller(client, module)
    event_stream_endpoint = "event-streams"
    event_stream_path = controller.get_endpoint(event_stream_endpoint)
    if event_stream_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.event_stream_info supports AAP 2.5 and onwards"
        )

    # Attempt to look up event_stream based on the provided name
    try:
        result = controller.get_one_or_many(
            event_stream_endpoint, name=name, want_one=False
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get event stream: {e}")

    module.exit_json(event_streams=result)


if __name__ == "__main__":
    main()
