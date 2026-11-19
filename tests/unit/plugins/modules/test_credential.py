# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib
import json
from typing import Any, Callable
from unittest.mock import MagicMock, Mock, patch

import pytest
from ansible.module_utils.common.parameters import remove_values
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAError,
)
from ansible_collections.ansible.eda.plugins.module_utils.redaction import (  # type: ignore
    protect_dict_values,
)

credential: Any = importlib.import_module(
    "ansible_collections.ansible.eda.plugins.modules.credential"
)

BuildModule = Callable[[dict[str, Any], dict[str, Any]], Any]

BASE_PARAMS: dict[str, Any] = {
    "name": "test-credential",
    "controller_host": "https://eda.example.com",
}

SCHEMA: dict[str, Any] = {
    "fields": [
        {"id": "username", "type": "string"},
        {"id": "password", "type": "string", "secret": True},
        {"id": "api_version", "type": "string"},
    ]
}

INPUTS: dict[str, Any] = {
    "username": "webhook-user",
    "password": "s3cr3t",
    "api_version": "v2",
}


def _build(build_module: BuildModule, inputs: Any) -> Any:
    params = dict(BASE_PARAMS)
    params["inputs"] = inputs
    return build_module(credential.build_argument_spec(), params)


def _protect(module: Any, credential_type: dict[str, Any]) -> None:
    """Run the same redaction steps main() performs."""
    protect_dict_values(module, "inputs")
    credential._protect_inputs(module, credential_type)


class TestArgumentSpec:
    def test_inputs_is_no_log(self) -> None:
        spec = credential.build_argument_spec()
        assert spec["inputs"]["type"] == "dict"
        assert spec["inputs"]["no_log"] is True


class TestProtectInputs:
    def test_masks_only_secret_fields(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(INPUTS))

        _protect(module, {"inputs": SCHEMA})

        assert isinstance(module.no_log_values, set)
        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values
        assert "v2" not in module.no_log_values

    def test_masks_everything_without_schema(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(INPUTS))

        _protect(module, {})

        assert set(INPUTS.values()) <= module.no_log_values

    def test_masks_everything_for_unknown_field(
        self, build_module: BuildModule
    ) -> None:
        inputs = dict(INPUTS)
        inputs["unexpected"] = "value"
        module = _build(build_module, inputs)

        _protect(module, {"inputs": SCHEMA})

        assert set(inputs.values()) <= module.no_log_values

    def test_masks_everything_for_untyped_schema(
        self, build_module: BuildModule
    ) -> None:
        module = _build(build_module, dict(INPUTS))

        _protect(module, {"inputs": {"required": ["password"]}})

        assert set(INPUTS.values()) <= module.no_log_values

    def test_string_inputs_are_masked(self, build_module: BuildModule) -> None:
        module = _build(
            build_module,
            '{"username": "webhook-user", "password": "s3cr3t"}',
        )

        _protect(module, {"inputs": SCHEMA})

        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values

    def test_no_inputs(self, build_module: BuildModule) -> None:
        module = build_module(credential.build_argument_spec(), dict(BASE_PARAMS))

        _protect(module, {"inputs": SCHEMA})

        assert module.no_log_values == set()


class TestMaskedResult:
    def test_secret_does_not_appear_in_result(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(INPUTS))
        _protect(module, {"inputs": SCHEMA})

        result = remove_values(
            {
                "invocation": {"module_args": module.params},
                "id": 42,
            },
            module.no_log_values,
        )
        dumped = json.dumps(result)

        assert "s3cr3t" not in dumped
        assert "webhook-user" in dumped
        assert "v2" in dumped

    def test_string_input_secret_does_not_appear_in_result(
        self, build_module: BuildModule
    ) -> None:
        module = _build(
            build_module,
            '{"username": "webhook-user", "password": "s3cr3t"}',
        )
        _protect(module, {"inputs": SCHEMA})

        result = remove_values(
            {"invocation": {"module_args": module.params}},
            module.no_log_values,
        )

        assert "s3cr3t" not in json.dumps(result)


class TestResolveCredentialType:
    def test_uses_credential_type_name(self) -> None:
        module = MagicMock()
        module.params = {"credential_type_name": "Basic Event Stream"}
        controller = MagicMock()
        controller.get_exactly_one.return_value = {"id": 7, "inputs": SCHEMA}

        result = credential._resolve_credential_type(module, controller, None)

        assert result == {"id": 7, "inputs": SCHEMA}
        controller.get_endpoint.assert_not_called()

    def test_uses_nested_credential_type(self) -> None:
        module = MagicMock()
        module.params = {}
        controller = MagicMock()
        response = MagicMock()
        response.status = 200
        response.json = {"id": 7, "inputs": SCHEMA}
        controller.get_endpoint.return_value = response

        result = credential._resolve_credential_type(
            module, controller, {"credential_type": {"id": 7}}
        )

        assert result == {"id": 7, "inputs": SCHEMA}
        controller.get_endpoint.assert_called_once_with("credential-types/7/")

    def test_uses_integer_credential_type(self) -> None:
        module = MagicMock()
        module.params = {}
        controller = MagicMock()
        response = MagicMock()
        response.status = 200
        response.json = {"id": 7}
        controller.get_endpoint.return_value = response

        result = credential._resolve_credential_type(
            module, controller, {"credential_type": 7}
        )

        assert result == {"id": 7}
        controller.get_endpoint.assert_called_once_with("credential-types/7/")

    def test_uses_credential_type_id(self) -> None:
        module = MagicMock()
        module.params = {}
        controller = MagicMock()
        response = MagicMock()
        response.status = 200
        response.json = {"id": 8}
        controller.get_endpoint.return_value = response

        result = credential._resolve_credential_type(
            module, controller, {"credential_type_id": 8}
        )

        assert result == {"id": 8}
        controller.get_endpoint.assert_called_once_with("credential-types/8/")

    def test_returns_empty_without_type(self) -> None:
        module = MagicMock()
        module.params = {}
        controller = MagicMock()

        result = credential._resolve_credential_type(module, controller, None)

        assert result == {}
        controller.get_endpoint.assert_not_called()

    def test_returns_empty_on_unsuccessful_response(self) -> None:
        module = MagicMock()
        module.params = {}
        controller = MagicMock()
        response = MagicMock()
        response.status = 404
        response.json = {}
        controller.get_endpoint.return_value = response

        result = credential._resolve_credential_type(
            module, controller, {"credential_type": {"id": 7}}
        )

        assert result == {}

    def test_fails_when_lookup_errors(self) -> None:
        module = MagicMock()
        module.params = {"credential_type_name": "missing"}
        module.fail_json.side_effect = SystemExit(1)
        controller = MagicMock()
        controller.get_exactly_one.side_effect = EDAError("boom")

        with pytest.raises(SystemExit):
            credential._resolve_credential_type(module, controller, None)

        assert (
            "Failed to lookup credential type"
            in module.fail_json.call_args.kwargs["msg"]
        )


class TestCreateParams:
    def test_uses_resolved_credential_type(self) -> None:
        module = MagicMock()
        module.params = {
            "description": "desc",
            "inputs": {"password": "s3cr3t"},
            "credential_type_name": "ignored",
            "organization_name": None,
        }
        controller = MagicMock()

        params = credential.create_params(module, controller, {"id": 7})

        assert params == {
            "description": "desc",
            "inputs": {"password": "s3cr3t"},
            "credential_type_id": 7,
        }
        controller.resolve_name_to_id.assert_not_called()

    @patch.object(credential, "lookup_resource_id", return_value=9)
    def test_looks_up_the_type_when_not_resolved(self, lookup: Mock) -> None:
        module = MagicMock()
        module.params = {
            "description": None,
            "inputs": None,
            "credential_type_name": "Basic Event Stream",
            "organization_name": None,
        }
        controller = MagicMock()

        params = credential.create_params(module, controller)

        assert params == {"credential_type_id": 9}
        lookup.assert_called_once_with(
            module, controller, "credential-types", "Basic Event Stream"
        )

    @patch.object(credential, "lookup_resource_id", return_value=3)
    def test_includes_organization(self, lookup: Mock) -> None:
        module = MagicMock()
        module.params = {
            "description": None,
            "inputs": None,
            "credential_type_name": None,
            "organization_name": "Default",
        }
        controller = MagicMock()

        params = credential.create_params(module, controller)

        assert params == {"organization_id": 3}
        lookup.assert_called_once_with(module, controller, "organizations", "Default")


class _AnsibleExit(Exception):
    pass


def _make_main_module(params: dict[str, Any]) -> MagicMock:
    module = MagicMock()
    module.params = params
    module.argument_spec = credential.build_argument_spec()
    module.no_log_values = set()
    module.check_mode = False
    module.exit_json.side_effect = _AnsibleExit
    module.fail_json.side_effect = _AnsibleExit
    return module


def _run_main(module: MagicMock, controller: MagicMock) -> None:
    with (
        patch.object(credential, "RedactingAnsibleModule", return_value=module),
        patch.object(credential, "Client", return_value=MagicMock()),
        patch.object(credential, "Controller", return_value=controller),
        pytest.raises(_AnsibleExit),
    ):
        credential.main()


class TestMain:
    @staticmethod
    def _params(**overrides: Any) -> dict[str, Any]:
        params: dict[str, Any] = {
            "name": "test-credential",
            "new_name": None,
            "copy_from": None,
            "description": None,
            "inputs": {"username": "webhook-user", "password": "s3cr3t"},
            "credential_type_name": "Basic Event Stream",
            "organization_name": None,
            "metadata": None,
            "state": "present",
            "controller_host": "https://eda.example.com",
        }
        params.update(overrides)
        return params

    def test_present_creates_credential(self) -> None:
        module = _make_main_module(self._params())
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {}
        controller.create_or_update_if_needed.return_value = {
            "changed": True,
            "id": 1,
        }

        _run_main(module, controller)

        controller.create_or_update_if_needed.assert_called_once()
        module.exit_json.assert_called_once_with(changed=True, id=1)

    def test_test_state_posts_to_endpoint(self) -> None:
        module = _make_main_module(self._params(state="test"))
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {"id": 7}
        response = MagicMock()
        response.status = 202
        response.json = {}
        controller.post_endpoint.return_value = response

        _run_main(module, controller)

        controller.post_endpoint.assert_called_once_with(
            "eda-credentials/7/test/", data={}
        )
        module.exit_json.assert_called_once()

    def test_absent_deletes_credential(self) -> None:
        module = _make_main_module(self._params(state="absent"))
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {"id": 7}
        controller.delete_if_needed.return_value = {"changed": True}

        _run_main(module, controller)

        controller.delete_if_needed.assert_called_once()
        module.exit_json.assert_called_once_with(changed=True)

    def test_copy_copies_credential(self) -> None:
        module = _make_main_module(self._params(copy_from="source"))
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {"id": 7}
        controller.copy_if_needed.return_value = {"changed": True}

        _run_main(module, controller)

        controller.copy_if_needed.assert_called_once()
        module.exit_json.assert_called_once_with(changed=True)
