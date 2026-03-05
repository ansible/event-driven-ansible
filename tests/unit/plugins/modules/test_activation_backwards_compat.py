# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import Mock, patch

import pytest
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAError,
)


@pytest.fixture
def mock_module() -> Mock:
    """Mock AnsibleModule for testing."""
    module = Mock()
    module.params = {
        "name": "test_activation",
        "project_name": "test_project",
        "rulebook_name": "test_rulebook.yml",
        "decision_environment_name": "test_de",
        "organization_name": "Default",
        "restart_on_project_update": True,
        "state": "present",
        "restart": False,
        "enabled": True,
    }
    module.check_mode = False
    module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    return module


@pytest.fixture
def mock_controller() -> Mock:
    """Mock Controller for testing."""
    controller = Mock()
    # Mock get_exactly_one to return empty dict (no existing activation)
    controller.get_exactly_one.return_value = {}
    return controller


def test_activation_graceful_failure_on_unsupported_restart_on_project_update(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test that rulebook_activation module fails gracefully when EDA server < 2.7
    doesn't support restart_on_project_update parameter.
    """
    # Mock the controller to raise an error similar to what an old server would return
    mock_controller.create_or_update_if_needed.side_effect = EDAError(
        "Failed to create/update rulebook activation: "
        "{'restart_on_project_update': ['Unknown field']}"
    )

    # Import and patch the module
    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            from ansible_collections.ansible.eda.plugins.modules import (  # type: ignore
                rulebook_activation,
            )

            # Mock lookup_resource_id to return IDs for resources
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
                side_effect=[1, 1, 1, 1],  # org_id, project_id, rulebook_id, de_id
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                    return_value=mock_module,
                ):
                    # Expect fail_json to be called with helpful message
                    with pytest.raises(SystemExit):
                        rulebook_activation.main()

                    # Verify fail_json was called
                    assert mock_module.fail_json.called
                    call_args = mock_module.fail_json.call_args[1]
                    error_msg = call_args["msg"]

                    # Verify the error message is helpful
                    assert (
                        "does not support" in error_msg
                        or "upgrade your EDA server" in error_msg
                        or "version 2.7" in error_msg
                    )
                    assert "restart_on_project_update" in error_msg


def test_activation_with_invalid_field_error_pattern(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test various error message patterns that indicate unsupported parameters.
    """
    # Test different error patterns from Django REST framework
    error_patterns = [
        "{'restart_on_project_update': ['Unknown field']}",
        "{'restart_on_project_update': ['This field is not allowed']}",
        "{'restart_on_project_update': ['Unrecognized field']}",
        "restart_on_project_update is not a valid field",
    ]

    for error_pattern in error_patterns:
        mock_controller.create_or_update_if_needed.side_effect = EDAError(
            f"Failed to create/update rulebook activation: {error_pattern}"
        )

        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
            return_value=mock_controller,
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
            ):
                from ansible_collections.ansible.eda.plugins.modules import (
                    rulebook_activation,
                )

                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
                    side_effect=[1, 1, 1, 1],
                ):
                    with patch(
                        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                        return_value=mock_module,
                    ):
                        with pytest.raises(SystemExit):
                            rulebook_activation.main()

                        assert mock_module.fail_json.called
                        call_args = mock_module.fail_json.call_args[1]
                        error_msg = call_args["msg"]

                        # Should provide helpful guidance
                        assert "restart_on_project_update" in error_msg


def test_activation_passes_through_other_errors(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test that non-version-related errors are passed through unchanged.
    """
    # Mock a different kind of error (not related to unsupported parameters)
    mock_controller.create_or_update_if_needed.side_effect = EDAError(
        "Failed to create/update rulebook activation: Database connection failed"
    )

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            from ansible_collections.ansible.eda.plugins.modules import (
                rulebook_activation,
            )

            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
                side_effect=[1, 1, 1, 1],
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                    return_value=mock_module,
                ):
                    with pytest.raises(SystemExit):
                        rulebook_activation.main()

                    assert mock_module.fail_json.called
                    call_args = mock_module.fail_json.call_args[1]
                    error_msg = call_args["msg"]

                    # Should contain the original error
                    assert "Database connection failed" in error_msg
