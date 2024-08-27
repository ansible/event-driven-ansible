#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: credential_info
author:
  - Alina Buzachis (@alinabuzachis)
short_description: List credentials in the EDA Controller
description:
    - List credentials in the EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - The name of the credential.
    type: str
    required: false
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - M(ansible.eda.credential_info) supports AAP 2.5 and onwards.
"""


EXAMPLES = """
  - name: Get information about a credential
    ansible.eda.credential_info:
      name: "Test"

  - name: List all credentials
    ansible.eda.credential_info:
"""


RETURN = """
credentials:
  description: Information about credentials.
  returned: always
  type: list
  elements: dict
  sample: [
    {
      "created_at": "2024-08-14T08:57:55.151787Z",
      "credential_type": {
        "id": 1,
        "kind": "scm",
        "name": "Source Control",
        "namespace": "scm"
      },
      "description": "This is a test credential",
      "id": 24,
      "inputs": {
        "password": "$encrypted$",
        "username": "testuser"
      },
      "managed": false,
      "modified_at": "2024-08-14T08:57:56.324925Z",
      "name": "New Test Credential",
      "organization": {
        "description": "The default organization",
        "id": 1,
        "name": "Default"
      },
      "references": null
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
    credential_endpoint = "eda-credentials"
    credential_path = controller.get_endpoint(credential_endpoint)
    if credential_path.status in (404,):
        module.fail_json(
            msg="Module ansible.eda.credential_info supports AAP 2.5 and onwards"
        )

    # Attempt to look up credential based on the provided name
    try:
        result = controller.get_one_or_many(
            credential_endpoint, name=name, want_one=False
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get credential: {e}")

    module.exit_json(credentials=result)


if __name__ == "__main__":
    main()
