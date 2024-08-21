# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Optional
from unittest.mock import MagicMock

import pytest
from ansible_collections.ansible.eda.plugins.module_utils.common import (  # type: ignore
    lookup_resource_id,
)
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAError,
)


# Define test cases as a list of tuples
@pytest.mark.parametrize(
    "endpoint, name, params, resolve_name_to_id_return, resolve_name_to_id_side_effect,"
    "expected_result, fail_json_called, fail_json_args",
    [
        (
            "test-endpoint",
            "test-name",
            {"param1": "value1"},
            "resource-id-123",
            None,
            "resource-id-123",
            False,
            None,
        ),
        (
            "test-endpoint",
            "test-name",
            None,
            None,
            EDAError("An error occurred"),
            None,
            True,
            {"msg": "Failed to lookup resource: An error occurred"},
        ),
    ],
)
def test_lookup_resource_id(
    endpoint: str,
    name: str,
    params: Optional[dict[str, Any]],
    resolve_name_to_id_return: Any,
    resolve_name_to_id_side_effect: Optional[Exception],
    expected_result: Optional[Any],
    fail_json_called: bool,
    fail_json_args: Optional[dict[str, Any]],
):
    mock_controller = MagicMock()
    mock_module = MagicMock()

    if resolve_name_to_id_side_effect:
        mock_controller.resolve_name_to_id.side_effect = resolve_name_to_id_side_effect
    else:
        mock_controller.resolve_name_to_id.return_value = resolve_name_to_id_return

    # Run the function and handle the exception case
    if fail_json_called:
        lookup_resource_id(
            module=mock_module,
            controller=mock_controller,
            endpoint=endpoint,
            name=name,
            params=params,
        )
        # Verify that fail_json was called with the expected arguments
        mock_module.fail_json.assert_called_once_with(**fail_json_args)
    else:
        result = lookup_resource_id(
            module=mock_module,
            controller=mock_controller,
            endpoint=endpoint,
            name=name,
            params=params,
        )
        assert result == expected_result
        mock_module.fail_json.assert_not_called()
