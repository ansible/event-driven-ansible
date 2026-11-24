# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml
from ansible_collections.ansible.eda.plugins.modules.rulebook_activation import (  # type: ignore
    format_extra_vars,
)

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
