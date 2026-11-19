# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from typing import Any, Callable

import pytest
from ansible.module_utils.common.parameters import remove_values
from ansible_collections.ansible.eda.plugins.module_utils.redaction import (  # type: ignore
    RedactingAnsibleModule,
    leaf_values,
    protect_dict_values,
    secret_field_ids,
)

BuildModule = Callable[..., Any]

INPUTS_SPEC: dict[str, Any] = {"inputs": {"type": "dict", "no_log": True}}

SCHEMA: dict[str, Any] = {
    "fields": [
        {"id": "username", "type": "string"},
        {"id": "password", "type": "string", "secret": True},
        {"id": "token", "type": "string", "secret": False},
    ]
}


class TestLeafValues:
    def test_string(self) -> None:
        assert list(leaf_values("s3cr3t")) == ["s3cr3t"]
        assert list(leaf_values("")) == []

    def test_nested(self) -> None:
        value = {
            "a": "1",
            "b": {"c": "2"},
            "d": ["3", {"e": "4"}],
        }
        assert set(leaf_values(value)) == {"1", "2", "3", "4"}

    def test_numbers(self) -> None:
        assert set(leaf_values({"port": 8200, "ratio": 1.5})) == {"8200", "1.5"}

    def test_skips_bool_and_none(self) -> None:
        value = {"enabled": True, "disabled": False, "missing": None}
        assert list(leaf_values(value)) == []

    def test_skips_keys(self) -> None:
        assert list(leaf_values({"a-secret-key": "value"})) == ["value"]

    def test_plain_scalar(self) -> None:
        assert list(leaf_values("value")) == ["value"]
        assert list(leaf_values(42)) == ["42"]


class TestSecretFieldIds:
    def test_only_secret_true(self) -> None:
        assert secret_field_ids(SCHEMA) == {"password"}

    def test_missing_schema(self) -> None:
        assert secret_field_ids(None) == set()
        assert secret_field_ids({}) == set()

    def test_metadata_section(self) -> None:
        schema = {
            "fields": [{"id": "password", "secret": True}],
            "metadata": [
                {"id": "secret_path"},
                {"id": "api_key", "secret": True},
            ],
        }
        assert secret_field_ids(schema, section="metadata") == {"api_key"}

    def test_malformed_entries_are_ignored(self) -> None:
        schema = {
            "fields": [
                "not-a-field",
                {"secret": True},
                {"id": "password", "secret": True},
            ]
        }
        assert secret_field_ids(schema) == {"password"}


class TestProtectDictValues:
    def test_no_log_values_is_a_mutable_set(self, build_module: BuildModule) -> None:
        """protect_dict_values rewrites module.no_log_values in place.

        ansible-core does not document this attribute. If it stops being a
        mutable set, the redaction helper (and this test) must be revisited.
        """
        module = build_module(INPUTS_SPEC, {"inputs": {"password": "s3cr3t"}})

        assert isinstance(module.no_log_values, set)
        assert hasattr(module.no_log_values, "difference_update")

        original = module.no_log_values
        protect_dict_values(module, "inputs", {"password"})
        assert module.no_log_values is original

    def test_registers_every_value_when_unknown(
        self, build_module: BuildModule
    ) -> None:
        module = build_module(
            INPUTS_SPEC,
            {"inputs": {"username": "webhook-user", "password": "s3cr3t"}},
        )

        masked = protect_dict_values(module, "inputs")

        assert masked == {"webhook-user", "s3cr3t"}
        assert module.no_log_values == {"webhook-user", "s3cr3t"}

    def test_narrows_to_secret_fields(self, build_module: BuildModule) -> None:
        module = build_module(
            INPUTS_SPEC,
            {
                "inputs": {
                    "username": "webhook-user",
                    "password": "s3cr3t",
                    "api_version": "v2",
                }
            },
        )

        masked = protect_dict_values(module, "inputs", {"password"})

        assert masked == {"s3cr3t"}
        assert module.no_log_values == {"s3cr3t"}
        assert "webhook-user" not in module.no_log_values
        assert "v2" not in module.no_log_values

    def test_string_parameter_is_registered(self, build_module: BuildModule) -> None:
        """A dict supplied as a JSON string is coerced after no_log values
        are collected, which used to leave it completely unprotected."""
        module = build_module(
            INPUTS_SPEC,
            {"inputs": '{"username": "webhook-user", "password": "s3cr3t"}'},
        )
        assert module.params["inputs"] == {
            "username": "webhook-user",
            "password": "s3cr3t",
        }

        protect_dict_values(module, "inputs")
        protect_dict_values(module, "inputs", {"password"})

        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values

    def test_keeps_values_of_other_no_log_parameters(
        self, build_module: BuildModule
    ) -> None:
        spec = {
            "inputs": {"type": "dict", "no_log": True},
            "controller_password": {"type": "str", "no_log": True},
        }
        module = build_module(
            spec,
            {
                "inputs": {"username": "webhook-user", "password": "s3cr3t"},
                "controller_password": "auth-secret",
            },
        )

        protect_dict_values(module, "inputs", {"password"})

        assert module.no_log_values == {"s3cr3t", "auth-secret"}

    def test_collision_with_other_no_log_parameter_stays_masked(
        self, build_module: BuildModule
    ) -> None:
        spec = {
            "inputs": {"type": "dict", "no_log": True},
            "controller_password": {"type": "str", "no_log": True},
        }
        module = build_module(
            spec,
            {
                "inputs": {"username": "shared-value", "password": "s3cr3t"},
                "controller_password": "shared-value",
            },
        )

        protect_dict_values(module, "inputs", {"password"})

        # The value is still needed to mask controller_password.
        assert "shared-value" in module.no_log_values
        assert "s3cr3t" in module.no_log_values

    def test_empty_inputs(self, build_module: BuildModule) -> None:
        module = build_module(INPUTS_SPEC, {"inputs": None})
        assert protect_dict_values(module, "inputs", {"password"}) == set()

    def test_non_mapping_value_is_registered(self, build_module: BuildModule) -> None:
        module = build_module({"inputs": {"type": "raw"}}, {"inputs": "raw-secret"})

        masked = protect_dict_values(module, "inputs")

        assert masked == {"raw-secret"}
        assert module.no_log_values == {"raw-secret"}


class TestMaskedResult:
    def test_only_secret_values_are_removed(self, build_module: BuildModule) -> None:
        module = build_module(
            INPUTS_SPEC,
            {
                "inputs": {
                    "username": "webhook-user",
                    "password": "s3cr3t",
                    "api_version": "v2",
                }
            },
        )
        protect_dict_values(module, "inputs", {"password"})

        result = remove_values(
            {"invocation": {"module_args": module.params}},
            module.no_log_values,
        )
        dumped = json.dumps(result)

        assert "s3cr3t" not in dumped
        assert "webhook-user" in dumped
        assert "v2" in dumped

    def test_string_parameter_is_removed_from_result(
        self, build_module: BuildModule
    ) -> None:
        module = build_module(
            INPUTS_SPEC,
            {"inputs": '{"username": "webhook-user", "password": "s3cr3t"}'},
        )
        protect_dict_values(module, "inputs")

        result = remove_values(
            {"invocation": {"module_args": module.params}},
            module.no_log_values,
        )

        assert "s3cr3t" not in json.dumps(result)


class TestRedactingAnsibleModule:
    def test_fail_json_registers_coerced_values(
        self, build_module: BuildModule
    ) -> None:
        module = build_module(
            INPUTS_SPEC,
            {"inputs": '{"password": "s3cr3t"}'},
            RedactingAnsibleModule,
        )
        # A validation failure exits from inside __init__, so the
        # post-construction marker has not been set yet.
        module._no_log_ready = False

        with pytest.raises(SystemExit):
            module.fail_json(msg="missing required arguments: name")

        result = remove_values(
            {"invocation": {"module_args": module.params}},
            module.no_log_values,
        )
        assert "s3cr3t" not in json.dumps(result)

    def test_exit_keeps_narrowed_values(self, build_module: BuildModule) -> None:
        module = build_module(
            INPUTS_SPEC,
            {"inputs": {"username": "webhook-user", "password": "s3cr3t"}},
            RedactingAnsibleModule,
        )
        protect_dict_values(module, "inputs", {"password"})

        with pytest.raises(SystemExit):
            module.exit_json(changed=True)

        result = remove_values(
            {"invocation": {"module_args": module.params}},
            module.no_log_values,
        )
        dumped = json.dumps(result)

        assert "s3cr3t" not in dumped
        assert "webhook-user" in dumped
