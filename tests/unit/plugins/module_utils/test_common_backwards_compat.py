# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import Mock

import pytest
from ansible_collections.ansible.eda.plugins.module_utils.common import (  # type: ignore
    handle_api_error,
)
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAError,
)


@pytest.fixture
def mock_module() -> Mock:
    """Mock AnsibleModule."""
    module = Mock()
    module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    return module


def test_handle_api_error_with_multiple_unsupported_params(mock_module: Mock) -> None:
    """Test detection of multiple unsupported parameters."""
    error = EDAError(
        "{'update_revision_on_launch': ['Unknown field'], 'scm_update_cache_timeout': ['Invalid field']}"
    )

    with pytest.raises(SystemExit):
        handle_api_error(
            mock_module,
            error,
            new_params=["update_revision_on_launch", "scm_update_cache_timeout"],
            min_version="2.7",
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    error_msg = call_args["msg"]

    # Should mention both parameters
    assert (
        "update_revision_on_launch" in error_msg
        or "scm_update_cache_timeout" in error_msg
    )
    assert "2.7" in error_msg


@pytest.mark.parametrize(
    "error_message",
    [
        "{'restart_on_project_update': ['Unknown field']}",
        "{'restart_on_project_update': ['unexpected field']}",
        "{'restart_on_project_update': ['not allowed']}",
        "{'restart_on_project_update': ['invalid field']}",
        "{'restart_on_project_update': ['unrecognized field']}",
    ],
)
def test_handle_api_error_recognizes_error_patterns(
    mock_module: Mock, error_message: str
) -> None:
    """Test that various Django REST framework error patterns are recognized."""
    error = EDAError(error_message)

    with pytest.raises(SystemExit):
        handle_api_error(
            mock_module,
            error,
            new_params=["restart_on_project_update"],
            min_version="2.7",
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    error_msg = call_args["msg"]

    # Should provide helpful error message
    assert "restart_on_project_update" in error_msg
    assert "2.7" in error_msg


def test_handle_api_error_passes_through_unrelated_errors(mock_module: Mock) -> None:
    """Test that errors unrelated to version compatibility are passed through."""
    error = EDAError("Network timeout occurred")

    with pytest.raises(SystemExit):
        handle_api_error(
            mock_module,
            error,
            new_params=["update_revision_on_launch"],
            min_version="2.7",
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    error_msg = call_args["msg"]

    # Should contain the original error message
    assert "Network timeout occurred" in error_msg
    # Should NOT provide version upgrade guidance
    assert "upgrade" not in error_msg.lower()


def test_handle_api_error_case_insensitive(mock_module: Mock) -> None:
    """Test that error detection is case-insensitive."""
    error = EDAError("{'Update_Revision_On_Launch': ['UNKNOWN FIELD']}")

    with pytest.raises(SystemExit):
        handle_api_error(
            mock_module,
            error,
            new_params=["update_revision_on_launch"],
            min_version="2.7",
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    error_msg = call_args["msg"]

    # Should detect despite case differences
    assert "update_revision_on_launch" in error_msg
