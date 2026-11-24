# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml
from ansible_collections.ansible.eda.plugins.modules.rulebook_activation import (  # type: ignore
    create_params,
    extra_vars_are_equal,
    format_extra_vars,
)

MODULE_PATH = "ansible_collections.ansible.eda.plugins.modules.rulebook_activation"

EXTRA_VARS = {"zeta": 1, "alpha": {"nothing": None, "path": "C:\\temp"}}


class _AnsibleExit(Exception):
    """Simulates module.fail_json halting execution."""


def test_format_extra_vars_keeps_dict_values() -> None:
    result = format_extra_vars(MagicMock(), EXTRA_VARS)

    assert yaml.safe_load(result) == EXTRA_VARS


def test_format_extra_vars_matches_api_formatting() -> None:
    # The API returns extra_var as yaml.dump() of the parsed value
    result = format_extra_vars(MagicMock(), EXTRA_VARS)

    assert result == yaml.dump(yaml.safe_load(result))


def test_format_extra_vars_passes_strings_through() -> None:
    value = '{"zeta": 1}'

    assert format_extra_vars(MagicMock(), value) == value


@pytest.mark.parametrize("value", [["a", "b"], 1, True])
def test_format_extra_vars_rejects_other_types(value: Any) -> None:
    module = MagicMock()
    module.fail_json.side_effect = _AnsibleExit

    with pytest.raises(_AnsibleExit):
        format_extra_vars(module, value)

    module.fail_json.assert_called_once()


@pytest.mark.parametrize(
    "old, new",
    [
        ("alpha: 1\nzeta: 2\n", "zeta: 2\nalpha: 1"),
        ("alpha: 1\nzeta: 2\n", '{"zeta": 2, "alpha": 1}'),
        ("alpha:\n  nothing: null\n", "{alpha: {nothing: ~}}"),
        ("", None),
        ("", "{}"),
        (None, "{}\n"),
        ("{}\n", ""),
    ],
)
def test_extra_vars_are_equal_same_content(old: Any, new: Any) -> None:
    assert extra_vars_are_equal(old, new)


@pytest.mark.parametrize(
    "old, new",
    [
        ("alpha: 1\n", "alpha: 2"),
        ("alpha: 1\n", "alpha: 1\nzeta: 2"),
        ("alpha: 1\n", ""),
        ("alpha: 1\n", "alpha: [1"),
        ("flag: true\n", '{"flag": 1}'),
        ("limit: 1\n", '{"limit": true}'),
        ("ratio: 1\n", "ratio: 1.0"),
        ("items: [1, true]\n", "items: [true, 1]"),
        ("nested:\n  flag: false\n", "nested: {flag: 0}"),
    ],
)
def test_extra_vars_are_equal_different_content(old: Any, new: Any) -> None:
    assert not extra_vars_are_equal(old, new)


def _activation_params(extra_vars: Any) -> dict[str, Any]:
    """Build activation parameters with the given extra_vars."""
    module = MagicMock()
    module.params = {
        "project_name": "project",
        "rulebook_name": "rulebook.yml",
        "decision_environment_name": "de",
        "organization_name": "Default",
        "state": "present",
        "extra_vars": extra_vars,
    }
    with patch(f"{MODULE_PATH}.lookup_resource_id", return_value=1):
        return dict(create_params(module, MagicMock(), is_aap_24=True))


@pytest.mark.parametrize(
    "extra_vars, extra_var",
    [({}, "{}\n"), ("", ""), ({"alpha": 1}, "alpha: 1\n")],
)
def test_create_params_sends_given_extra_vars(extra_vars: Any, extra_var: str) -> None:
    assert _activation_params(extra_vars)["extra_var"] == extra_var


def test_create_params_leaves_omitted_extra_vars_out() -> None:
    assert "extra_var" not in _activation_params(None)
