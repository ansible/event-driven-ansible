# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib
import json
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest
from ansible.module_utils.common.parameters import remove_values
from ansible_collections.ansible.eda.plugins.module_utils.redaction import (  # type: ignore
    protect_dict_values,
)

credential_type: Any = importlib.import_module(
    "ansible_collections.ansible.eda.plugins.modules.credential_type"
)

BuildModule = Callable[[dict[str, Any], dict[str, Any]], Any]

BASE_PARAMS: dict[str, Any] = {
    "name": "Test Credential Type",
    "controller_host": "https://eda.example.com",
    "state": "test",
}

SCHEMA: dict[str, Any] = {
    "fields": [
        {"id": "username", "type": "string"},
        {"id": "password", "type": "string", "secret": True},
        {"id": "api_version", "type": "string"},
    ]
}

TEST_INPUTS: dict[str, Any] = {
    "username": "webhook-user",
    "password": "s3cr3t",
    "api_version": "v2",
}


def _build(build_module: BuildModule, test_inputs: Any) -> Any:
    params = dict(BASE_PARAMS)
    params["test_inputs"] = test_inputs
    return build_module(credential_type.build_argument_spec(), params)


def _protect(module: Any, credential_type_object: dict[str, Any]) -> None:
    """Run the same redaction steps main() performs."""
    protect_dict_values(module, "test_inputs")
    credential_type._protect_test_inputs(module, credential_type_object)


class TestArgumentSpec:
    def test_test_inputs_is_no_log(self) -> None:
        spec = credential_type.build_argument_spec()
        assert spec["test_inputs"]["type"] == "dict"
        assert spec["test_inputs"]["no_log"] is True

    def test_schema_parameters_are_not_no_log(self) -> None:
        spec = credential_type.build_argument_spec()
        assert "no_log" not in spec["inputs"]
        assert "no_log" not in spec["injectors"]
        assert "no_log" not in spec["test_metadata"]


class TestProtectTestInputs:
    def test_masks_only_secret_fields(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(TEST_INPUTS))

        _protect(module, {"inputs": SCHEMA})

        assert isinstance(module.no_log_values, set)
        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values
        assert "v2" not in module.no_log_values

    def test_masks_everything_without_schema(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(TEST_INPUTS))

        _protect(module, {})

        assert set(TEST_INPUTS.values()) <= module.no_log_values

    def test_masks_everything_for_unknown_field(
        self, build_module: BuildModule
    ) -> None:
        test_inputs = dict(TEST_INPUTS)
        test_inputs["unexpected"] = "value"
        module = _build(build_module, test_inputs)

        _protect(module, {"inputs": SCHEMA})

        assert set(test_inputs.values()) <= module.no_log_values

    def test_string_inputs_are_masked(self, build_module: BuildModule) -> None:
        module = _build(
            build_module,
            '{"username": "webhook-user", "password": "s3cr3t"}',
        )

        _protect(module, {"inputs": SCHEMA})

        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values

    def test_no_test_inputs(self, build_module: BuildModule) -> None:
        module = build_module(credential_type.build_argument_spec(), dict(BASE_PARAMS))

        _protect(module, {"inputs": SCHEMA})

        assert module.no_log_values == set()


class TestMaskedResult:
    def test_secret_does_not_appear_in_result(self, build_module: BuildModule) -> None:
        module = _build(build_module, dict(TEST_INPUTS))
        _protect(module, {"inputs": SCHEMA})

        result = remove_values(
            {
                "invocation": {"module_args": module.params},
                "test_result": {"success": False},
            },
            module.no_log_values,
        )
        dumped = json.dumps(result)

        assert "s3cr3t" not in dumped
        assert "webhook-user" in dumped
        assert "v2" in dumped

    def test_string_test_inputs_secret_does_not_appear_in_result(
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


class _AnsibleExit(Exception):
    pass


def _make_main_module(params: dict[str, Any]) -> MagicMock:
    module = MagicMock()
    module.params = params
    module.argument_spec = credential_type.build_argument_spec()
    module.no_log_values = set()
    module.check_mode = False
    module.exit_json.side_effect = _AnsibleExit
    module.fail_json.side_effect = _AnsibleExit
    return module


def _run_main(module: MagicMock, controller: MagicMock) -> None:
    with (
        patch.object(credential_type, "RedactingAnsibleModule", return_value=module),
        patch.object(credential_type, "Client", return_value=MagicMock()),
        patch.object(credential_type, "Controller", return_value=controller),
        pytest.raises(_AnsibleExit),
    ):
        credential_type.main()


class TestMain:
    @staticmethod
    def _params(**overrides: Any) -> dict[str, Any]:
        params: dict[str, Any] = {
            "name": "Test Credential Type",
            "new_name": None,
            "description": None,
            "inputs": {"fields": SCHEMA["fields"]},
            "injectors": None,
            "test_inputs": None,
            "test_metadata": None,
            "state": "present",
            "controller_host": "https://eda.example.com",
        }
        params.update(overrides)
        return params

    def test_present_creates_type(self) -> None:
        module = _make_main_module(self._params())
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {
            "id": 1,
            "name": "Test Credential Type",
            "inputs": SCHEMA,
        }
        controller.create_or_update_if_needed.return_value = {
            "changed": True,
            "id": 1,
        }

        _run_main(module, controller)

        controller.create_or_update_if_needed.assert_called_once()
        module.exit_json.assert_called_once_with(changed=True, id=1)

    def test_test_state_posts_to_endpoint(self) -> None:
        module = _make_main_module(
            self._params(state="test", test_inputs=dict(TEST_INPUTS))
        )
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {
            "id": 1,
            "name": "Test Credential Type",
            "inputs": SCHEMA,
        }
        response = MagicMock()
        response.status = 202
        response.json = {}
        controller.post_endpoint.return_value = response

        _run_main(module, controller)

        controller.post_endpoint.assert_called_once()
        module.exit_json.assert_called_once()

    def test_absent_deletes_type(self) -> None:
        module = _make_main_module(self._params(state="absent"))
        controller = MagicMock()
        controller.get_endpoint.return_value.status = 200
        controller.get_exactly_one.return_value = {
            "id": 1,
            "name": "Test Credential Type",
            "inputs": SCHEMA,
        }
        controller.delete_if_needed.return_value = {"changed": True}

        _run_main(module, controller)

        controller.delete_if_needed.assert_called_once()
        module.exit_json.assert_called_once_with(changed=True)
