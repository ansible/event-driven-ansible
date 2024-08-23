#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: activation
author:
  - "Nikhil Jain (@jainnikhil30)"
  - "Alina Buzachis (@alinabuzachis)"
short_description: Manage rulebook activations in the EDA Controller
description:
  - This module allows the user to create or delete rulebook activations in the EDA Controller.
options:
  name:
    description:
      - The name of the rulebook activation.
    type: str
    required: true
  description:
    description:
      - The description of the rulebook activation.
    type: str
  project_name:
    description:
      - The name of the project associated with the rulebook activation.
    type: str
    aliases:
      - project
  rulebook_name:
    description:
      - The name of the rulebook associated with the rulebook activation.
    type: str
    aliases:
      - rulebook
  extra_vars:
    description:
      - The extra variables for the rulebook activation.
    type: str
  restart_policy:
    description:
      - The restart policy for the rulebook activation.
    default: "always"
    choices: ["on-failure", "always", "never"]
    type: str
  enabled:
    description:
      - Whether the rulebook activation is enabled or not.
    type: bool
    default: true
  decision_environment_name:
    description:
      - The name of the decision environment associated with the rulebook activation.
    type: str
    aliases:
      - decision_environment
  awx_token_name:
    description:
      - The token ID of the AWX controller.
    type: str
    aliases:
      - awx_token
      - token
  organization_name:
    description:
      - The name of the organization.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: str
    aliases:
      - organization
  eda_credentials:
    description:
      - A list of IDs for EDA credentials used by the rulebook activation.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: list
    elements: str
    aliases:
      - credentials
  k8s_service_name:
    description:
      - The name of the Kubernetes service associated with this rulebook activation.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: str
  webhooks:
    description:
      - A list of webhook IDs associated with the rulebook activation.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: list
    elements: str
  swap_single_source:
    description:
      - Allow swapping of single sources in a rulebook without name match.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: bool
    default: true
  event_streams:
    description:
      -  A list of IDs representing the event streams that this rulebook activation listens to.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: list
    elements: int
  log_level:
    description:
      - Allow setting the desired log level.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: str
    default: "debug"
    choices: ["debug", "info", "error"]
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - Rulebook Activation API does not support PATCH method, due to this reason the module will
    not perform any modification when an existing rulebook activation is found.
"""

EXAMPLES = """
- name: Create a rulebook activation
  ansible.eda.activation:
    name: "Example Rulebook Activation"
    description: "Example Rulebook Activation description"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    enabled: False
    awx_token_name: "Example Token"

- name: Delete a rulebook activation
  ansible.eda.activation:
    name: "Example Rulebook Activation"
    state: absent
"""


RETURN = """
id:
  description: ID of the rulebook activation.
  returned: when exists
  type: int
  sample: 37
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def create_params(
    module: AnsibleModule, controller: Controller, is_aap_24: bool
) -> dict[str, Any]:
    activation_params: dict[str, Any] = {}

    # Get the project id
    project_id = None
    if module.params.get("project_name"):
        project_id = lookup_resource_id(
            module, controller, "projects", module.params["project_name"]
        )
    if project_id is not None:
        activation_params["project_id"] = project_id

    # Get the rulebook id
    rulebook_id = None
    params = {}
    if project_id is not None:
        params = {"data": {"project_id": project_id}}
    if module.params.get("rulebook_name"):
        rulebook_id = lookup_resource_id(
            module,
            controller,
            "rulebooks",
            module.params["rulebook_name"],
            params,
        )
    if rulebook_id is not None:
        activation_params["rulebook_id"] = rulebook_id

    # Get the decision environment id
    decision_environment_id = None
    if module.params.get("decision_environment_name"):
        decision_environment_id = lookup_resource_id(
            module,
            controller,
            "decision-environments",
            module.params["decision_environment_name"],
        )
    if decision_environment_id is not None:
        activation_params["decision_environment_id"] = decision_environment_id

    # Get the organization id
    organization_id = None
    if not is_aap_24 and module.params.get("organization_name"):
        organization_id = lookup_resource_id(
            module, controller, "organizations", module.params["organization_name"]
        )
    if organization_id is not None:
        activation_params["organization_id"] = organization_id

    if module.params.get("description"):
        activation_params["description"] = module.params["description"]

    if module.params.get("extra_vars"):
        activation_params["extra_var"] = module.params["extra_vars"]

    # Get the AWX token id
    awx_token_id = None
    if module.params.get("awx_token_name"):
        awx_token_id = lookup_resource_id(
            module, controller, "/users/me/awx-tokens/", module.params["awx_token_name"]
        )
    if awx_token_id is not None:
        activation_params["awx_token_id"] = awx_token_id

    if module.params.get("restart_policy"):
        activation_params["restart_policy"] = module.params["restart_policy"]

    if module.params.get("enabled"):
        activation_params["is_enabled"] = module.params["enabled"]

    if not is_aap_24 and module.params.get("event_streams"):
        activation_params["event_streams"] = module.params["event_streams"]

    # Get the eda credential ids
    eda_credential_ids = None
    if not is_aap_24 and module.params.get("eda_credentials"):
        eda_credential_ids = []
        for item in module.params["eda_credentials"]:
            cred_id = lookup_resource_id(module, controller, "eda-credentials", item)
            if cred_id is not None:
                eda_credential_ids.append(cred_id)

    if eda_credential_ids is not None:
        activation_params["eda_credentials"] = eda_credential_ids

    if not is_aap_24 and module.params.get("k8s_service_name"):
        activation_params["k8s_service_name"] = module.params["k8s_service_name"]

    # Get the webhook ids
    webhooks_ids = None
    if not is_aap_24 and module.params.get("webhooks"):
        webhooks_ids = []
        for item in module.params["webhooks"]:
            webhook_id = lookup_resource_id(module, controller, "webhooks", item)
            if webhook_id is not None:
                webhooks_ids.append(webhook_id)
    if webhooks_ids is not None:
        activation_params["webhooks"] = webhooks_ids

    if not is_aap_24 and module.params.get("log_level"):
        activation_params["log_level"] = module.params["log_level"]

    if not is_aap_24 and module.params.get("swap_single_source"):
        activation_params["swap_single_source"] = module.params["swap_single_source"]

    return activation_params


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        description=dict(type="str"),
        project_name=dict(type="str", aliases=["project"]),
        rulebook_name=dict(type="str", aliases=["rulebook"]),
        extra_vars=dict(type="str"),
        restart_policy=dict(
            type="str",
            default="always",
            choices=[
                "on-failure",
                "always",
                "never",
            ],
        ),
        enabled=dict(type="bool", default=True),
        decision_environment_name=dict(type="str", aliases=["decision_environment"]),
        awx_token_name=dict(type="str", aliases=["awx_token", "token"]),
        organization_name=dict(type="str", aliases=["organization"]),
        event_streams=dict(type="list", elements="int"),
        eda_credentials=dict(type="list", elements="str", aliases=["credentials"]),
        k8s_service_name=dict(type="str"),
        webhooks=dict(type="list", elements="str"),
        swap_single_source=dict(type="bool", default=True),
        log_level=dict(type="str", choices=["debug", "info", "error"], default="debug"),
        state=dict(choices=["present", "absent"], default="present"),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [
        (
            "state",
            "present",
            ("name", "rulebook_name", "decision_environment_name"),
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

    name = module.params.get("name")
    state = module.params.get("state")

    controller = Controller(client, module)
    # Organization is not available in Controller 2.4 API
    config_endpoint_avail = controller.get_endpoint(
        "config",
    )
    is_aap_24 = config_endpoint_avail.status in (404,)
    organization_name = module.params.get("organization_name")
    if state == "present" and not is_aap_24 and organization_name is None:
        module.fail_json(
            msg="Parameter organization_name is required when state is present."
        )
    # Attempt to find rulebook activation based on the provided name
    try:
        activation = controller.get_exactly_one("activations", name=name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook activation: {e}")

    if state == "absent":
        try:
            result = controller.delete_if_needed(activation, endpoint="activations")
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete rulebook activation: {e}")

    if activation:
        module.exit_json(
            msg=f"A rulebook activation with name: {name} already exists. "
            "The module does not support modifying a rulebook activation.",
            **{"changed": False, "id": activation["id"]},
        )

    # Activation Data that will be sent for create/update
    activation_params = create_params(module, controller, is_aap_24=is_aap_24)
    activation_params["name"] = (
        controller.get_item_name(activation) if activation else name
    )

    # If the state was present and we can let the module build or update the
    # existing activation, this will return on its own
    try:
        result = controller.create_if_needed(
            activation_params,
            endpoint="activations",
            item_type="activation",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update rulebook activation: {e}")


if __name__ == "__main__":
    main()
