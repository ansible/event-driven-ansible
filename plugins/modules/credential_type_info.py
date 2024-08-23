#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: credential_type_info
author:
  - Alina Buzachis (@alinabuzachis)
short_description: List credential types in EDA Controller
description:
  - List credential types in EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - The name of the credential type.
    type: str
    required: false
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_type_info) supports AAP 2.5 and onwards.
"""


EXAMPLES = """
  - name: Get information about a credential type
    ansible.eda.credential_type_info:
      name: "Test"

  - name: List all credential types
    ansible.eda.credential_type_info:
"""


RETURN = """
credential_types:
  description: Information about the credential types.
  returned: always
  type: list
  elements: dict
  sample: [{
    "created_at": "2024-08-14T08:30:14.806638Z",
    "description": "A test credential type",
    "id": 37,
    "injectors": {
      "extra_vars": {
          "field1": "field1"
      }
    },
    "inputs": {
      "fields": [
          {
            "id": "field1",
            "label": "Field 5",
            "type": "string"
          }
      ]
    },
    "kind": "cloud",
    "managed": false,
    "modified_at": "2024-08-14T08:30:14.807549Z",
    "name": "Example",
    "namespace": null
  }]
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
    credential_type_endpoint = "credential-types"
    credential_type_path = controller.get_endpoint(credential_type_endpoint)
    if credential_type_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.credential_type_info supports AAP 2.5 and onwards"
        )

    # Attempt to look up credential_type based on the provided name
    try:
        result = controller.get_one_or_many(
            credential_type_endpoint, name=name, want_one=False
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get credential type: {e}")

    module.exit_json(credential_types=result)


if __name__ == "__main__":
    main()
