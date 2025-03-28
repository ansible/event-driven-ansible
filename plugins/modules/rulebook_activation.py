#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: rulebook_activation
author:
  - "Nikhil Jain (@jainnikhil30)"
  - "Alina Buzachis (@alinabuzachis)"
short_description: Manage rulebook activations in the EDA Controller
description:
  - This module allows the user to create, delete, or restart rulebook activations in the EDA Controller.
options:
  name:
    description:
      - The name of the rulebook activation.
    type: str
    required: true
  new_name:
    description:
      - Renames an existing rulebook activation.
      - If set, the rulebook activation will be updated with the new name.
    type: str
    version_added: 2.7.0
  description:
    description:
      - The description of the rulebook activation.
    type: str
  project_name:
    description:
      - The name of the project associated with the rulebook activation.
      - Required when state is present.
    type: str
    aliases:
      - project
  rulebook_name:
    description:
      - The name of the rulebook associated with the rulebook activation.
      - Required when state is present.
    type: str
    aliases:
      - rulebook
  extra_vars:
    description:
      - The extra variables for the rulebook activation.
    type: str
  restart:
    description:
      - Performs a restart of the activation. This is a non idempotent operation.
      - If enabled the rest of parameters will be ignored.
    type: bool
    default: false
    version_added: 2.7.0
  restart_policy:
    description:
      - The restart policy for the rulebook activation.
    default: "on-failure"
    choices: ["on-failure", "always", "never"]
    type: str
  enabled:
    description:
      - Whether the rulebook activation is enabled or not.
      - This field will be removed in version 3.0.0.
      - The logic of controlling the state of an activation is going to be controlled
        by the C(state) parameter itself.
    type: bool
    default: true
  decision_environment_name:
    description:
      - The name of the decision environment associated with the rulebook activation.
      - Required when state is present.
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
      - The name of the organization. Required when state is present.
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
  swap_single_source:
    description:
      - Allow swapping of single sources in a rulebook without name match.
      - This parameter is no longer used and is going to be ignored.
      - This field will be removed in version 3.0.0.
    type: bool
    default: true
  event_streams:
    description:
      - A list of event stream names that this rulebook activation listens to.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: list
    elements: dict
    suboptions:
      event_stream:
        description:
          - The name of the event stream.
        type: str
      source_name:
        description:
          - The name of the source. It can be the name defined in the rulebook or the generated one by
            the API if the rulebook has not defined one, in this case the name can be retrieved with
            M(ansible.eda.rulebook_info) module.
          - O(event_streams.source_name) and O(event_streams.source_index) are mutually exclusive.
        type: str
      source_index:
        description:
          - The index of the source.
          - O(event_streams.source_name) and O(event_streams.source_index) are mutually exclusive.
        type: int
  log_level:
    description:
      - Allow setting the desired log level.
      - This parameter is supported in AAP 2.5 and onwards.
        If specified for AAP 2.4, value will be ignored.
    type: str
    default: "error"
    choices: ["debug", "info", "error"]
  state:
    description:
      - Desired state of the resource.
      - The state of an activation itself is controlled by this parameter, whether I(enabled) or
        I(disabled).
      - When an activation is created, it is I(enabled) by default. Thus, I(present) is equivalent to
        I(enabled).
      - Whether I(present), I(enabled), or I(disabled) is specified, an activation will be created if it
        doesn't exist already.
      - To create a disabled activation, specify C(state) as I(disabled).
      - Essentially, this parameter deprecates the usage of C(enabled).
    default: "present"
    choices: ["present", "absent", "disabled", "enabled"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
"""

EXAMPLES = r"""
- name: Create a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    description: "Example Rulebook Activation description"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    state: disabled

- name: Create a rulebook activation with event_streams option
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    description: "Example Activation description"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    state: disabled
    organization_name: "Default"
    event_streams:
      - event_stream: "Example Event Stream"
        source_name: "Sample source"

- name: Rename a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    new_name: "Example Rulebook Activation New Name"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Update a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    log_level: debug
    restart_policy: always
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Enable a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    state: enabled

- name: Disable a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    new_name: "Example Rulebook Activation New Name"
    state: disabled

- name: Restart activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation - Restart"
    organization_name: "Default"
    restart: true

- name: Delete a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    state: absent
"""


RETURN = r"""
id:
  description: ID of the rulebook activation.
  returned: when exists
  type: int
  sample: 37
"""

import traceback
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    HAS_YAML = False
    YAML_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_YAML = True
    YAML_IMPORT_ERROR = ""

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

from ..module_utils.arguments import AUTH_ARGSPEC
from ..module_utils.client import Client
from ..module_utils.common import lookup_resource_id
from ..module_utils.controller import Controller
from ..module_utils.errors import EDAError


def find_matching_source(
    event: Dict[str, Any], sources: List[Dict[str, Any]], module: AnsibleModule
) -> Dict[str, Any]:
    """
    Finds a matching source based on the source_name in the event.
    Raises an error if no match is found.
    """
    # Get the source_name from the event
    source_name = event.get("source_name")

    # Search for the matching source in the list of sources
    for source in sources:
        if source["name"] == source_name:
            return source  # Return the matching source if found

    # If no match is found, raise an error
    module.fail_json(msg=f"The specified source_name {source_name} does not exist.")

    return {}  # Explicit return to satisfy mypy


def process_event_streams(
    rulebook_id: int,
    controller: Controller,
    module: AnsibleModule,
) -> List[Dict[str, Any]]:
    """
    Processes event streams and updates activation_params with source mappings.

    Args:
        rulebook_id: The ID of the rulebook.
        controller: The controller object used for API calls.
        module: The module object, typically for error handling.

    Returns:
        List source mappings.
    """

    source_mappings = []

    try:
        sources = controller.get_one_or_many(
            f"rulebooks/{rulebook_id}/sources", name=module.params["rulebook_name"]
        )
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook source list: {e}")

    # Process each event_stream
    for event in module.params.get("event_streams"):
        source_mapping = {}

        # Check mutually exclusive conditions
        if event.get("source_index") and event.get("source_name"):
            module.fail_json(
                msg="source_index and source_name options are mutually exclusive."
            )

        if event.get("source_index") is None and event.get("source_name") is None:
            module.fail_json(
                msg="You must specify one of the options: source_index or source_name."
            )

        # Handle source_index
        if event.get("source_index") is not None:
            try:
                source_mapping["source_name"] = sources[event["source_index"]].get(
                    "name"
                )
                source_mapping["rulebook_hash"] = sources[event["source_index"]].get(
                    "rulebook_hash"
                )
            except IndexError as e:
                module.fail_json(
                    msg=f"The specified source_index {event['source_index']} is out of range: {e}"
                )

        # Handle source_name
        elif event.get("source_name"):
            matching_source = find_matching_source(event, sources, module)
            source_mapping["source_name"] = matching_source.get("name")
            source_mapping["rulebook_hash"] = matching_source.get("rulebook_hash")

        if event.get("event_stream") is None:
            module.fail_json(msg="You must specify an event stream name.")

        # Lookup event_stream_id
        event_stream_id = lookup_resource_id(
            module,
            controller,
            "event-streams",
            event["event_stream"],
        )

        if event_stream_id is None:
            module.fail_json(
                msg=f"The event stream {event['event_stream']} does not exist."
            )

        # Add the event stream to the source mapping
        source_mapping["event_stream_name"] = event["event_stream"]
        source_mapping["event_stream_id"] = event_stream_id
        source_mappings.append(source_mapping)

    return source_mappings


def create_params(
    module: AnsibleModule, controller: Controller, is_aap_24: bool
) -> Dict[str, Any]:
    activation_params: Dict[str, Any] = {}

    # Get the project id, only required to get the rulebook id
    project_name = module.params["project_name"]
    project_id = lookup_resource_id(module, controller, "projects", project_name)

    if project_id is None:
        module.fail_json(msg=f"Project {project_name} not found.")

    # Get the rulebook id
    rulebook_name = module.params["rulebook_name"]
    params = {"data": {"project_id": project_id}}
    rulebook_id = lookup_resource_id(
        module,
        controller,
        "rulebooks",
        rulebook_name,
        params,
    )
    if rulebook_id is None:
        module.fail_json(
            msg=f"Rulebook {rulebook_name} not found for project {project_name}."
        )

    activation_params["rulebook_id"] = rulebook_id

    # Get the decision environment id
    decision_environment_name = module.params["decision_environment_name"]
    decision_environment_id = lookup_resource_id(
        module,
        controller,
        "decision-environments",
        decision_environment_name,
    )
    if decision_environment_id is None:
        module.fail_json(
            msg=f"Decision Environment {decision_environment_name} not found."
        )
    activation_params["decision_environment_id"] = decision_environment_id

    # Get the organization id
    organization_name = module.params["organization_name"]
    if not is_aap_24:
        organization_id = lookup_resource_id(
            module, controller, "organizations", organization_name
        )
        if organization_id is None:
            module.fail_json(msg=f"Organization {organization_name} not found.")
        activation_params["organization_id"] = organization_id

    # Get the AWX token id
    awx_token_id = None
    if module.params.get("awx_token_name"):
        awx_token_id = lookup_resource_id(
            module, controller, "/users/me/awx-tokens/", module.params["awx_token_name"]
        )
    if awx_token_id is not None:
        activation_params["awx_token_id"] = awx_token_id

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

    if not is_aap_24 and module.params.get("event_streams"):
        # Process event streams and source mappings
        activation_params["source_mappings"] = yaml.dump(
            process_event_streams(
                # ignore type error, if rulebook_id is None, it will fail earlier
                rulebook_id=rulebook_id,  # type: ignore[arg-type]
                controller=controller,
                module=module,
            )
        )

    # Set the remaining parameters
    if module.params.get("description"):
        activation_params["description"] = module.params["description"]

    if module.params.get("extra_vars"):
        activation_params["extra_var"] = module.params["extra_vars"]

    if module.params.get("restart_policy"):
        activation_params["restart_policy"] = module.params["restart_policy"]

    if module.params.get("state") == "disabled":
        activation_params["is_enabled"] = False
    else:
        activation_params["is_enabled"] = True

    if not is_aap_24 and module.params.get("log_level"):
        activation_params["log_level"] = module.params["log_level"]

    return activation_params


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        project_name=dict(type="str", aliases=["project"]),
        rulebook_name=dict(type="str", aliases=["rulebook"]),
        extra_vars=dict(type="str"),
        restart=dict(type="bool", default=False),
        restart_policy=dict(
            type="str",
            default="on-failure",
            choices=[
                "on-failure",
                "always",
                "never",
            ],
        ),
        enabled=dict(
            type="bool",
            default=True,
            removed_in_version="3.0.0",
            removed_from_collection="ansible.eda",
        ),
        decision_environment_name=dict(type="str", aliases=["decision_environment"]),
        awx_token_name=dict(type="str", aliases=["awx_token", "token"]),
        organization_name=dict(type="str", aliases=["organization"]),
        eda_credentials=dict(type="list", elements="str", aliases=["credentials"]),
        k8s_service_name=dict(type="str"),
        event_streams=dict(
            type="list",
            elements="dict",
            options=dict(
                event_stream=dict(type="str"),
                source_index=dict(type="int"),
                source_name=dict(type="str"),
            ),
        ),
        swap_single_source=dict(
            type="bool",
            default=True,
            removed_in_version="3.0.0",
            removed_from_collection="ansible.eda",
        ),
        log_level=dict(type="str", choices=["debug", "info", "error"], default="error"),
        state=dict(
            choices=["present", "absent", "enabled", "disabled"], default="present"
        ),
    )

    # Define the state the activation is transitioning to, and uses
    # this in the call to the according post endpoint.
    # Returns an empty string in case the state is not changing.
    def endpoint_state(activation: Dict[str, Any], state: str) -> str:
        return {(False, "enabled"): "enable", (True, "disabled"): "disable"}.get(
            (activation["is_enabled"], state), ""
        )

    argument_spec.update(AUTH_ARGSPEC)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    restart = module.params.get("restart", None)

    if not HAS_YAML:
        module.fail_json(
            msg=missing_required_lib("pyyaml"), exception=YAML_IMPORT_ERROR
        )

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    name = module.params.get("name")
    new_name = module.params.get("new_name")
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
            msg=(
                "Parameter organization_name is required when state "
                "is present for this version of EDA."
            ),
        )
    # Attempt to find rulebook activation based on the provided name
    activation = {}
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

    if restart:
        try:
            result = controller.restart_if_needed(
                activation,
                endpoint=f"activations/{activation['id']}/restart",
            )
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to restart rulebook activation: {e}.")

    # Parse credential IDs in existing activation
    if activation:
        credential_ids = [
            credential_id["id"] for credential_id in activation["eda_credentials"]
        ]
        activation["eda_credentials"] = credential_ids

    if state and state in ("enabled", "disabled") and activation:
        change_state = endpoint_state(activation=activation, state=state)

        if change_state:
            try:
                # Call disable or enable endpoint
                endpoint = f"activations/{activation['id']}/{change_state}"
                controller.post_endpoint(endpoint=endpoint)
                module.exit_json(changed=True)
            except EDAError as e:
                module.fail_json(
                    msg=f"Failed to enable/disable rulebook activation: {e}"
                )

        module.exit_json(changed=False)

    # Activation Data that will be sent for create/update
    activation_params = create_params(module, controller, is_aap_24=is_aap_24)
    activation_params["name"] = (
        new_name
        if new_name
        else (controller.get_item_name(activation) if activation else name)
    )

    # If the state was one of (present, enabled or disabled), and we can let the module
    # build or update the existing activation, this will return on its own
    try:
        result = controller.create_or_update_if_needed(
            activation,
            activation_params,
            endpoint="activations",
            item_type="activation",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create/update rulebook activation: {e}")


if __name__ == "__main__":
    main()
