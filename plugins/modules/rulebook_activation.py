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
  - This module allows the user to create or delete rulebook activations in the EDA Controller.
options:
  name:
    description:
      - The name of the rulebook activation.
    type: str
    required: true
  new_name:
    description:
      - Setting this option will change the existing name.
    type: str
  copy_from:
    description:
      - Name to copy the rulebook activation from.
      - This will copy an existing rulebook activation and change any parameters supplied.
      - The new rulebook activation name will be the one provided in the name parameter.
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
  restart_policy:
    description:
      - The restart policy for the rulebook activation.
    choices: ["on-failure", "always", "never"]
    type: str
  enabled:
    description:
      - Whether the rulebook activation is enabled or not.
      - This field will be removed in version 3.0.0.
    type: bool
    default: false
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
    choices: ["debug", "info", "error"]
  state:
    description:
      - Desired state of the resource.
    default: "present"
    choices: ["present", "absent", "enabled", "disabled"]
    type: str
extends_documentation_fragment:
  - ansible.eda.eda_controller.auths
notes:
  - Rulebook Activation API does not support PATCH method, due to this reason the module will
    not perform any modification when an existing rulebook activation is found.
"""

EXAMPLES = r"""
- name: Create a rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    description: "Example Rulebook Activation description"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    eda_credentials:
        - My AAP Credentials
    organization_name: "Default"

- name: Create a rulebook activation with event_streams option
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    description: "Example Activation description"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"
    eda_credentials:
        - My AAP Credentials
    event_streams:
      - event_stream: "Example Event Stream"
        source_name: "Sample source"

- name: Update rulebook activation fields
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation"
    eda_credentials:
        - My AAP credential
        - My other credential
    log_level: debug
    restart_policy: always
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Copy an existing rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation - copy"
    copy_from: "Example Rulebook Activation"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Rename rulebook activation
  ansible.eda.rulebook_activation:
    name: "Example Rulebook Activation - copy"
    new_name: "Renamed Example Rulebook Activation"
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Enable activation
  ansible.eda.rulebook_activation:
    name: "Renamed Example Rulebook Activation"
    state: enabled
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

- name: Disable activation
  ansible.eda.rulebook_activation:
    name: "Renamed Example Rulebook Activation"
    state: disabled
    project_name: "Example Project"
    rulebook_name: "hello_controller.yml"
    decision_environment_name: "Example Decision Environment"
    organization_name: "Default"

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

NO_OP = "noop"


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

    if module.params.get("enabled") is not None:
        activation_params["is_enabled"] = module.params["enabled"]

    if not is_aap_24 and module.params.get("log_level"):
        activation_params["log_level"] = module.params["log_level"]

    if module.params.get("state"):
        activation_params["state"] = module.params["state"]

    return activation_params


def check_operation(
    activation: dict[str, Any], activation_params: dict[str, Any]
) -> str:
    """
    Check if the user wants to disable or enable an existing activation.

    Args:
        activation: Existing activation.
        activation_params: Parameters passed in the module.

    Returns:
        String of the desired operation, either 'enable' or 'disable'.
    """

    operation = {
        ("enabled", "disabled"): "disable",
        ("disabled", "enabled"): "enable",
    }.get((activation["state"], activation_params["state"]), NO_OP)

    return operation


def main() -> None:
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        copy_from=dict(type="str"),
        description=dict(type="str"),
        project_name=dict(type="str", aliases=["project"]),
        rulebook_name=dict(type="str", aliases=["rulebook"]),
        extra_vars=dict(type="str"),
        restart_policy=dict(
            type="str",
            choices=[
                "on-failure",
                "always",
                "never",
            ],
        ),
        enabled=dict(
            type="bool",
            default=False,
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
        log_level=dict(type="str", choices=["debug", "info", "error"]),
        state=dict(
            choices=["present", "absent", "enabled", "disabled"], default="present"
        ),
    )

    argument_spec.update(AUTH_ARGSPEC)

    required_if = [
        (
            "state",
            "present",
            ("name", "rulebook_name", "decision_environment_name", "project_name"),
        )
    ]

    module = AnsibleModule(
        argument_spec=argument_spec, required_if=required_if, supports_check_mode=True
    )

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
    copy_from = module.params.get("copy_from")
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
        activation = controller.get_exactly_one("activations", name=copy_from if copy_from else name)
    except EDAError as e:
        module.fail_json(msg=f"Failed to get rulebook activation: {e}")

    if state == "absent":
        try:
            result = controller.delete_if_needed(activation, endpoint="activations")
            module.exit_json(**result)
        except EDAError as e:
            module.fail_json(msg=f"Failed to delete rulebook activation: {e}")

    # Activation Data that will be sent for create/update
    activation_params = create_params(module, controller, is_aap_24=is_aap_24)
    activation_params["name"] = new_name if new_name else name

    # Handle copies before anything else
    if copy_from:
        if not activation:
            module.fail_json(msg=f"Activation with name {copy_from} was not found.")
        else:
            try:
                copy_endpoint = f"activations/{activation["id"]}/copy"
                params = {"name": name}

                controller.post_endpoint(
                    endpoint=copy_endpoint,
                    data=params
                )
                module.exit_json(changed=True)
            except EDAError as e:
                module.fail_json(msg=f"Failed to copy rulebook activation: {e}")

    if activation:

        # Define 'state' of existing activation, and remove 'enabled' from
        # constructed parameters to avoid unnecessary updates.
        activation["state"] = "enabled" if activation["is_enabled"] else "disabled"
        activation_params.pop("is_enabled", None)
        activation_params.pop("enabled", None)

        # Change from list of credentials to a list of IDs in existing activation
        credential_ids = [credential_id["id"] for credential_id in activation["eda_credentials"]]
        activation["eda_credentials"] = credential_ids

        if controller.objects_could_be_different(activation, activation_params):
            try:
                op_type = check_operation(activation, activation_params)

                # NOTE(kaiokmo): In order to avoid the user enabling/disabling and
                # also updating an activation altogether in one shot, first we handle
                # the operation enable/disable, then we exit. This is needed because, for now,
                # we are not directly managing the state of an activation.
                #
                # This doesn't handle cases where the user tries to update an activation
                # while it's still enabled. We simply honor the operation first before
                # anything else.
                if op_type != NO_OP:
                    enable_disable_endpoint = (
                        f"activations/{activation["id"]}/{op_type}"
                    )
                    controller.post_endpoint(endpoint=enable_disable_endpoint)
                    module.exit_json(changed=True)

                result = controller.update_if_needed(
                    activation,
                    activation_params,
                    endpoint="activations",
                    item_type="activation",
                )
                module.exit_json(**result)
            except EDAError as e:
                module.fail_json(msg=f"Failed to update rulebook activation: {e}")
        else:
            module.exit_json(changed=False)

    try:
        result = controller.create_if_needed(
            activation_params,
            endpoint="activations",
            item_type="activation",
        )
        module.exit_json(**result)
    except EDAError as e:
        module.fail_json(msg=f"Failed to create rulebook activation: {e}")


if __name__ == "__main__":
    main()
