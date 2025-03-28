#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: rulebook_activation_copy
author:
  - "Kaio Oliveira (@kaiokmo)"
  - "Brandon W (@b-whitt)"
short_description: Copy rulebook activations in the EDA Controller
description:
  - This module allows the user to copy rulebook activations in the EDA Controller.
version_added: 2.7.0
options:
  name:
    description:
      - The name of the new rulebook activation.
    type: str
    required: true
  copy_from:
    description:
      - Name of the existing rulebook activation to copy.
    type: str
    required: true
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: Copy an existing rulebook activation
  ansible.eda.rulebook_activation_copy:
    name: "Example Rulebook Activation - copy"
    copy_from: "Example Rulebook Activation"
"""

RETURN = r"""
id:
  description: ID of the rulebook activation.
  returned: when exists
  type: int
  sample: 37
"""


from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        copy_from=dict(type="str", required=True),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    copy_from = module.params.get("copy_from")

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    name = module.params.get("name")
    controller = Controller(client, module)

    # Attempt to find rulebook activation based on the provided name
    activation = {}
    try:
        activation = controller.get_exactly_one("activations", name=copy_from)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook activation: {e}")

    try:
        result = controller.copy_if_needed(
            name,
            copy_from,
            endpoint=f"activations/{activation['id']}/copy",
            item_type="activation",
        )
        module.exit_json(**result)
    except KeyError as e:
        module.fail_json(msg=f"Unable to access {e} of the activation to copy from.")
    except EDAError as e:
        module.fail_json(msg=f"Failed to copy rulebook activation: {e}")


if __name__ == "__main__":
    main()
