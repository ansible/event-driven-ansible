# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible.module_utils.common.parameters import remove_values

from ansible_collections.ansible.eda.plugins.modules import credential
from ansible_collections.ansible.eda.plugins.module_utils.redaction import (
    protect_dict_values,
)

BASE_PARAMS = {
    "name": "test-credential",
    "controller_host": "https://eda.example.com",
}

SCHEMA = {
    "fields": [
        {"id": "username", "type": "string"},
        {"id": "password", "type": "string", "secret": True},
        {"id": "api_version", "type": "string"},
    ]
}

INPUTS = {
    "username": "webhook-user",
    "password": "s3cr3t",
    "api_version": "v2",
}


def _build(build_module, inputs):
    params = dict(BASE_PARAMS)
    params["inputs"] = inputs
    return build_module(credential.build_argument_spec(), params)


def _protect(module, credential_type):
    """Run the same redaction steps main() performs."""
    protect_dict_values(module, "inputs")
    credential._protect_inputs(module, credential_type)


class TestArgumentSpec:
    def test_inputs_is_no_log(self):
        spec = credential.build_argument_spec()
        assert spec["inputs"]["type"] == "dict"
        assert spec["inputs"]["no_log"] is True


class TestProtectInputs:
    def test_masks_only_secret_fields(self, build_module):
        module = _build(build_module, dict(INPUTS))

        _protect(module, {"inputs": SCHEMA})

        assert isinstance(module.no_log_values, set)
        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values
        assert "v2" not in module.no_log_values

    def test_masks_everything_without_schema(self, build_module):
        module = _build(build_module, dict(INPUTS))

        _protect(module, {})

        assert set(INPUTS.values()) <= module.no_log_values

    def test_masks_everything_for_unknown_field(self, build_module):
        inputs = dict(INPUTS)
        inputs["unexpected"] = "value"
        module = _build(build_module, inputs)

        _protect(module, {"inputs": SCHEMA})

        assert set(inputs.values()) <= module.no_log_values

    def test_masks_everything_for_untyped_schema(self, build_module):
        module = _build(build_module, dict(INPUTS))

        _protect(module, {"inputs": {"required": ["password"]}})

        assert set(INPUTS.values()) <= module.no_log_values

    def test_string_inputs_are_masked(self, build_module):
        module = _build(
            build_module,
            '{"username": "webhook-user", "password": "s3cr3t"}',
        )

        _protect(module, {"inputs": SCHEMA})

        assert "s3cr3t" in module.no_log_values
        assert "webhook-user" not in module.no_log_values

    def test_no_inputs(self, build_module):
        module = build_module(credential.build_argument_spec(), dict(BASE_PARAMS))

        _protect(module, {"inputs": SCHEMA})

        assert module.no_log_values == set()


class TestMaskedResult:
    def test_secret_does_not_appear_in_result(self, build_module):
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

    def test_string_input_secret_does_not_appear_in_result(self, build_module):
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
