# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib
import json
from typing import Any, Callable

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
