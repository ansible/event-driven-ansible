#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: activation_info
author:
  - Alina Buzachis (@alinabuzachis)
short_description: List rulebook activations in the EDA Controller
description:
    - List rulebook activations in the EDA controller.
version_added: 2.0.0
options:
  name:
    description:
      - The name of the rulebook activation.
    type: str
    required: false
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
"""


EXAMPLES = """
  - name: Get information about a rulebook activation
    ansible.eda.activation_info:
      name: "Example Rulebook Activation"

  - name: List all rulebook activations
    ansible.eda.activation_info:
"""


RETURN = """
activations:
  description: Information about rulebook activations.
  returned: always
  type: list
  elements: dict
  sample: [
    {
      "id": 1,
      "name": "Test activation",
      "description": "A test activation",
      "is_enabled": true,
      "status": "running",
      "extra_var": "",
      "decision_environment_id": 1,
      "project_id": 2,
      "rulebook_id": 1,
      "organization_id": 1,
      "restart_policy": "on-failure",
      "restart_count": 2,
      "rulebook_name": "Test rulebook",
      "current_job_id": "2",
      "rules_count": 2,
      "rules_fired_count": 2,
      "created_at": "2024-08-10T14:22:30.123Z",
      "modified_at": "2024-08-15T11:45:00.987Z",
      "status_message": "Activation is running successfully.",
      "awx_token_id": 1,
      "event_streams": [],
      "log_level": "info",
      "eda_credentials": [],
      "k8s_service_name": "",
      "webhooks": [],
      "swap_single_source": false
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

    # Attempt to look up credential based on the provided name
    try:
        result = controller.get_one_or_many("activations", name=name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook activations: {e}")

    module.exit_json(activations=result)


if __name__ == "__main__":
    main()
