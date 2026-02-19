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


def test_create_params_includes_restart_on_project_update_when_true() -> None:
    """
    Test that restart_on_project_update is included in params when True.
    """
    from ansible_collections.ansible.eda.plugins.modules import (
        rulebook_activation,
    )

    # Mock module with restart_on_project_update = True
    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "description": "test description",
        "restart_policy": "always",
        "state": "enabled",
        "restart_on_project_update": True,
        "log_level": "info",
        "project_name": "test_project",
        "rulebook_name": "test_rulebook.yml",
        "decision_environment_name": "test_de",
        "organization_name": "Default",
        "enabled": True,
    }
    mock_module.fail_json = Mock()

    # Mock controller
    mock_controller = Mock()

    # Mock lookup_resource_id to return IDs
    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
        side_effect=[1, 1, 1, 1],  # project_id, rulebook_id, de_id, org_id
    ):
        # Call create_params
        result = rulebook_activation.create_params(
            mock_module,
            controller=mock_controller,
            is_aap_24=False,
        )

    # Verify restart_on_project_update is in the result
    assert "restart_on_project_update" in result
    assert result["restart_on_project_update"] is True


def test_create_params_excludes_restart_on_project_update_when_false() -> None:
    """
    Test that restart_on_project_update is NOT included in params when False.
    """
    from ansible_collections.ansible.eda.plugins.modules import (
        rulebook_activation,
    )

    # Mock module with restart_on_project_update = False
    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "description": "test description",
        "restart_policy": "always",
        "state": "enabled",
        "restart_on_project_update": False,
        "log_level": "info",
        "project_name": "test_project",
        "rulebook_name": "test_rulebook.yml",
        "decision_environment_name": "test_de",
        "organization_name": "Default",
        "enabled": True,
    }
    mock_module.fail_json = Mock()

    # Mock controller
    mock_controller = Mock()

    # Mock lookup_resource_id to return IDs
    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
        side_effect=[1, 1, 1, 1],  # project_id, rulebook_id, de_id, org_id
    ):
        # Call create_params
        result = rulebook_activation.create_params(
            mock_module,
            controller=mock_controller,
            is_aap_24=False,
        )

    # Verify restart_on_project_update is NOT in the result
    assert "restart_on_project_update" not in result


def test_activation_successful_creation_with_restart_on_project_update(
    mock_controller: Mock,
) -> None:
    """
    Test successful activation creation with restart_on_project_update=True.
    """
    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "project_name": "test_project",
        "rulebook_name": "test_rulebook.yml",
        "decision_environment_name": "test_de",
        "organization_name": "Default",
        "restart_on_project_update": True,
        "state": "present",
        "restart": False,
        "enabled": True,
        "restart_policy": "always",
        "description": "test",
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock()

    # Mock successful creation
    mock_controller.get_exactly_one.return_value = {}
    mock_controller.create_or_update_if_needed.return_value = {
        "changed": True,
        "id": 123,
    }

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
                side_effect=[1, 1, 1, 1],  # org_id, project_id, rulebook_id, de_id
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                    return_value=mock_module,
                ):
                    rulebook_activation.main()

                    # Verify exit_json was called (success)
                    assert mock_module.exit_json.called

                    # Verify create_or_update_if_needed was called with params including restart_on_project_update
                    assert mock_controller.create_or_update_if_needed.called
                    call_args = mock_controller.create_or_update_if_needed.call_args
                    activation_params = call_args[0][1]  # Second positional argument
                    assert "restart_on_project_update" in activation_params
                    assert activation_params["restart_on_project_update"] is True


def test_find_matching_source_found() -> None:
    """Test find_matching_source when source is found."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    event = {"source_name": "test_source"}
    sources = [{"name": "test_source", "id": 1}, {"name": "other_source", "id": 2}]

    result = rulebook_activation.find_matching_source(event, sources, mock_module)

    assert result == {"name": "test_source", "id": 1}
    assert not mock_module.fail_json.called


def test_find_matching_source_not_found() -> None:
    """Test find_matching_source when source is not found."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    event = {"source_name": "nonexistent_source"}
    sources = [{"name": "test_source", "id": 1}]

    with pytest.raises(SystemExit):
        rulebook_activation.find_matching_source(event, sources, mock_module)

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    assert "nonexistent_source" in call_args["msg"]
    assert "does not exist" in call_args["msg"]


def test_process_event_streams_with_source_name() -> None:
    """Test process_event_streams using source_name."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "rulebook_name": "test_rulebook.yml",
        "event_streams": [
            {"source_name": "test_source", "event_stream": "test_stream"}
        ],
    }

    mock_controller = Mock()
    mock_controller.get_one_or_many.return_value = [
        {"name": "test_source", "rulebook_hash": "abc123"}
    ]

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
        return_value=1,
    ):
        result = rulebook_activation.process_event_streams(
            rulebook_id=1, controller=mock_controller, module=mock_module
        )

    assert len(result) == 1
    assert result[0]["source_name"] == "test_source"
    assert result[0]["event_stream_id"] == 1
    assert result[0]["event_stream_name"] == "test_stream"


def test_process_event_streams_with_source_index() -> None:
    """Test process_event_streams using source_index."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "rulebook_name": "test_rulebook.yml",
        "event_streams": [{"source_index": 0, "event_stream": "test_stream"}],
    }

    mock_controller = Mock()
    mock_controller.get_one_or_many.return_value = [
        {"name": "test_source", "rulebook_hash": "abc123"}
    ]

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
        return_value=1,
    ):
        result = rulebook_activation.process_event_streams(
            rulebook_id=1, controller=mock_controller, module=mock_module
        )

    assert len(result) == 1
    assert result[0]["source_name"] == "test_source"


def test_process_event_streams_source_index_out_of_range() -> None:
    """Test process_event_streams with invalid source_index."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    mock_module.params = {
        "rulebook_name": "test_rulebook.yml",
        "event_streams": [{"source_index": 10, "event_stream": "test_stream"}],
    }

    mock_controller = Mock()
    mock_controller.get_one_or_many.return_value = [
        {"name": "test_source", "rulebook_hash": "abc123"}
    ]

    with pytest.raises(SystemExit):
        rulebook_activation.process_event_streams(
            rulebook_id=1, controller=mock_controller, module=mock_module
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    assert "out of range" in call_args["msg"]


def test_process_event_streams_mutually_exclusive() -> None:
    """Test process_event_streams with both source_index and source_name."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    mock_module.params = {
        "rulebook_name": "test_rulebook.yml",
        "event_streams": [
            {
                "source_index": 1,  # Use 1 instead of 0 since 0 is falsy
                "source_name": "test_source",
                "event_stream": "test_stream",
            }
        ],
    }

    mock_controller = Mock()
    # Return a list of sources so subscripting works before the check
    mock_controller.get_one_or_many.return_value = [
        {"name": "test_source", "rulebook_hash": "abc123"},
        {"name": "test_source2", "rulebook_hash": "def456"},
    ]

    with pytest.raises(SystemExit):
        rulebook_activation.process_event_streams(
            rulebook_id=1, controller=mock_controller, module=mock_module
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    assert "mutually exclusive" in call_args["msg"]


def test_process_event_streams_missing_source_specification() -> None:
    """Test process_event_streams without source_index or source_name."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    mock_module.params = {
        "rulebook_name": "test_rulebook.yml",
        "event_streams": [{"event_stream": "test_stream"}],
    }

    mock_controller = Mock()
    # Return a list even though we're testing the error case
    mock_controller.get_one_or_many.return_value = [
        {"name": "test_source", "rulebook_hash": "abc123"}
    ]

    with pytest.raises(SystemExit):
        rulebook_activation.process_event_streams(
            rulebook_id=1, controller=mock_controller, module=mock_module
        )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    assert "must specify one of the options" in call_args["msg"]


def test_create_params_project_not_found() -> None:
    """Test create_params when project is not found."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    mock_module.params = {
        "project_name": "nonexistent_project",
        "rulebook_name": "test_rulebook.yml",
        "decision_environment_name": "test_de",
        "organization_name": "Default",
    }

    mock_controller = Mock()

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.lookup_resource_id",
        return_value=None,  # Project not found
    ):
        with pytest.raises(SystemExit):
            rulebook_activation.create_params(
                mock_module, controller=mock_controller, is_aap_24=False
            )

    assert mock_module.fail_json.called
    call_args = mock_module.fail_json.call_args[1]
    assert "Project" in call_args["msg"]
    assert "not found" in call_args["msg"]


def test_main_get_activation_failure() -> None:
    """Test main() when getting activation fails."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "present",
        "restart": False,
        "organization_name": "Default",
    }
    mock_module.check_mode = False
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.side_effect = EDAError("API connection failed")
    mock_controller.get_endpoint.return_value = Mock(status=200)

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_module.fail_json.called
                call_args = mock_module.fail_json.call_args[1]
                assert "Failed to get rulebook activation" in call_args["msg"]
                assert "API connection failed" in call_args["msg"]


def test_main_delete_activation() -> None:
    """Test main() for deleting an activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "absent",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {"id": 1, "name": "test_activation"}
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.delete_if_needed.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_controller.delete_if_needed.called
                assert mock_module.exit_json.called


def test_main_delete_activation_failure() -> None:
    """Test main() when deleting activation fails."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "absent",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {"id": 1, "name": "test_activation"}
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.delete_if_needed.side_effect = EDAError("Delete failed")

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_module.fail_json.called
                call_args = mock_module.fail_json.call_args[1]
                assert "Failed to delete rulebook activation" in call_args["msg"]


def test_main_restart_activation() -> None:
    """Test main() for restarting an activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "present",
        "restart": True,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": True,
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.restart_if_needed.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_controller.restart_if_needed.called
                assert mock_module.exit_json.called


def test_main_restart_activation_failure() -> None:
    """Test main() when restarting activation fails."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "present",
        "restart": True,
        "organization_name": "Default",
    }
    mock_module.check_mode = False
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": True,
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.restart_if_needed.side_effect = EDAError("Restart failed")

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_module.fail_json.called
                call_args = mock_module.fail_json.call_args[1]
                assert "Failed to restart rulebook activation" in call_args["msg"]


def test_main_enable_disabled_activation() -> None:
    """Test main() for enabling a disabled activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "enabled",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": False,
        "eda_credentials": [],
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.post_endpoint.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                # Should call post_endpoint to enable
                assert mock_controller.post_endpoint.called
                call_args = mock_controller.post_endpoint.call_args
                assert "enable" in call_args[1]["endpoint"]
                assert mock_module.exit_json.called


def test_main_disable_enabled_activation() -> None:
    """Test main() for disabling an enabled activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "disabled",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": True,
        "eda_credentials": [],
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.post_endpoint.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                # Should call post_endpoint to disable
                assert mock_controller.post_endpoint.called
                call_args = mock_controller.post_endpoint.call_args
                assert "disable" in call_args[1]["endpoint"]
                assert mock_module.exit_json.called


def test_main_enable_already_enabled_activation() -> None:
    """Test main() for enabling an already enabled activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "enabled",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": True,
        "eda_credentials": [],
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                # Should NOT call post_endpoint since already enabled
                assert not mock_controller.post_endpoint.called
                # Should exit with changed=False
                assert mock_module.exit_json.called
                call_args = mock_module.exit_json.call_args
                assert call_args[1]["changed"] is False


def test_main_enable_disable_failure() -> None:
    """Test main() when enable/disable fails."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "enabled",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.fail_json = Mock(side_effect=SystemExit("fail_json called"))

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": False,
        "eda_credentials": [],
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.post_endpoint.side_effect = EDAError("Enable failed")

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                assert mock_module.fail_json.called
                call_args = mock_module.fail_json.call_args[1]
                assert (
                    "Failed to enable/disable rulebook activation" in call_args["msg"]
                )


def test_main_parse_credential_ids() -> None:
    """Test main() parses credential IDs from existing activation."""
    from ansible_collections.ansible.eda.plugins.modules import rulebook_activation

    mock_module = Mock()
    mock_module.params = {
        "name": "test_activation",
        "state": "enabled",
        "restart": False,
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))

    mock_controller = Mock()
    # Activation with credentials in full object format
    mock_controller.get_exactly_one.return_value = {
        "id": 1,
        "name": "test_activation",
        "is_enabled": True,
        "eda_credentials": [
            {"id": 10, "name": "cred1"},
            {"id": 20, "name": "cred2"},
        ],
    }
    mock_controller.get_endpoint.return_value = Mock(status=200)

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Controller",
        return_value=mock_controller,
    ):
        with patch(
            "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.Client"
        ):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.rulebook_activation.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    rulebook_activation.main()

                # Should exit with changed=False since already enabled
                assert mock_module.exit_json.called
                call_args = mock_module.exit_json.call_args
                assert call_args[1]["changed"] is False
