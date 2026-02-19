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
        "name": "test_project",
        "url": "https://github.com/test/repo.git",
        "organization_name": "Default",
        "update_revision_on_launch": True,
        "scm_update_cache_timeout": 300,
        "state": "present",
    }
    module.check_mode = False
    module.fail_json = Mock(side_effect=SystemExit("fail_json called"))
    return module


@pytest.fixture
def mock_controller() -> Mock:
    """Mock Controller for testing."""
    controller = Mock()
    return controller


def test_project_graceful_failure_on_unsupported_update_revision_on_launch(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test that project module fails gracefully when EDA server < 2.7
    doesn't support update_revision_on_launch parameter.
    """
    # Mock the controller to raise an error similar to what an old server would return
    mock_controller.create_or_update_if_needed.side_effect = EDAError(
        "Unable to create project test_project: "
        "{'update_revision_on_launch': ['Unknown field']}"
    )

    # Import and patch the module
    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            from ansible_collections.ansible.eda.plugins.modules import (  # type: ignore
                project,
            )

            # Mock lookup_resource_id to return organization ID
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    # Expect fail_json to be called with helpful message
                    with pytest.raises(SystemExit):
                        project.main()

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
                    assert "update_revision_on_launch" in error_msg


def test_project_graceful_failure_on_unsupported_scm_update_cache_timeout(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test that project module fails gracefully when EDA server < 2.7
    doesn't support scm_update_cache_timeout parameter.
    """
    # Mock the controller to raise an error about scm_update_cache_timeout
    mock_controller.create_or_update_if_needed.side_effect = EDAError(
        "Unable to create project test_project: "
        "{'scm_update_cache_timeout': ['This field is not allowed']}"
    )

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            from ansible_collections.ansible.eda.plugins.modules import project

            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    with pytest.raises(SystemExit):
                        project.main()

                    assert mock_module.fail_json.called
                    call_args = mock_module.fail_json.call_args[1]
                    error_msg = call_args["msg"]

                    # Verify the error message mentions the parameter and version
                    assert "scm_update_cache_timeout" in error_msg
                    assert (
                        "2.7" in error_msg
                        or "upgrade" in error_msg.lower()
                        or "does not support" in error_msg
                    )


def test_project_passes_through_other_errors(
    mock_module: Mock, mock_controller: Mock
) -> None:
    """
    Test that non-version-related errors are passed through unchanged.
    """
    # Mock a different kind of error (not related to unsupported parameters)
    mock_controller.create_or_update_if_needed.side_effect = EDAError(
        "Unable to create project test_project: Network timeout"
    )

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            from ansible_collections.ansible.eda.plugins.modules import project

            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    with pytest.raises(SystemExit):
                        project.main()

                    assert mock_module.fail_json.called
                    call_args = mock_module.fail_json.call_args[1]
                    error_msg = call_args["msg"]

                    # Should contain the original error
                    assert "Network timeout" in error_msg


def test_project_excludes_update_revision_on_launch_when_false() -> None:
    """Test that update_revision_on_launch is excluded when False."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_module = Mock()
    mock_module.params = {
        "name": "test_project",
        "url": "https://github.com/test/repo.git",
        "organization_name": "Default",
        "update_revision_on_launch": False,
        "scm_update_cache_timeout": 3600,
        "state": "present",
        "description": "test",
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock()
    mock_module.fail_json = Mock()

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {}
    mock_controller.create_or_update_if_needed.return_value = {"changed": True, "id": 1}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    project.main()

                    # Verify create_or_update_if_needed was called
                    assert mock_controller.create_or_update_if_needed.called
                    call_args = mock_controller.create_or_update_if_needed.call_args
                    project_params = call_args[0][1]

                    # update_revision_on_launch should NOT be in params when False
                    assert "update_revision_on_launch" not in project_params


def test_project_excludes_scm_update_cache_timeout_when_zero() -> None:
    """Test that scm_update_cache_timeout is excluded when 0."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_module = Mock()
    mock_module.params = {
        "name": "test_project",
        "url": "https://github.com/test/repo.git",
        "organization_name": "Default",
        "update_revision_on_launch": True,
        "scm_update_cache_timeout": 0,
        "state": "present",
        "description": "test",
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock()
    mock_module.fail_json = Mock()

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {}
    mock_controller.create_or_update_if_needed.return_value = {"changed": True, "id": 1}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    project.main()

                    # Verify create_or_update_if_needed was called
                    assert mock_controller.create_or_update_if_needed.called
                    call_args = mock_controller.create_or_update_if_needed.call_args
                    project_params = call_args[0][1]

                    # scm_update_cache_timeout should NOT be in params when 0
                    assert "scm_update_cache_timeout" not in project_params


def test_project_includes_both_params_when_truthy() -> None:
    """Test that both params are included when truthy."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_module = Mock()
    mock_module.params = {
        "name": "test_project",
        "url": "https://github.com/test/repo.git",
        "organization_name": "Default",
        "update_revision_on_launch": True,
        "scm_update_cache_timeout": 3600,
        "state": "present",
        "description": "test",
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock()
    mock_module.fail_json = Mock()

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {}
    mock_controller.create_or_update_if_needed.return_value = {"changed": True, "id": 1}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    project.main()

                    # Verify create_or_update_if_needed was called
                    assert mock_controller.create_or_update_if_needed.called
                    call_args = mock_controller.create_or_update_if_needed.call_args
                    project_params = call_args[0][1]

                    # Both should be in params
                    assert "update_revision_on_launch" in project_params
                    assert project_params["update_revision_on_launch"] is True
                    assert "scm_update_cache_timeout" in project_params
                    assert project_params["scm_update_cache_timeout"] == 3600


def test_project_delete_state() -> None:
    """Test project deletion."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_module = Mock()
    mock_module.params = {
        "name": "test_project",
        "state": "absent",
    }
    mock_module.check_mode = False
    # Make exit_json exit immediately to stop execution
    mock_module.exit_json = Mock(side_effect=SystemExit("exit_json called"))
    mock_module.fail_json = Mock()

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {"id": 1, "name": "test_project"}
    mock_controller.get_endpoint.return_value = Mock(status=200)
    mock_controller.delete_if_needed.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                return_value=mock_module,
            ):
                with pytest.raises(SystemExit):
                    project.main()

                # Verify delete_if_needed was called
                assert mock_controller.delete_if_needed.called
                # Verify exit_json was called
                assert mock_module.exit_json.called


def test_project_sync_existing() -> None:
    """Test syncing an existing project."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_module = Mock()
    mock_module.params = {
        "name": "test_project",
        "sync": True,
        "state": "present",
        "url": "https://github.com/test/repo.git",
    }
    mock_module.check_mode = False
    mock_module.exit_json = Mock()
    mock_module.fail_json = Mock()

    mock_controller = Mock()
    mock_controller.get_exactly_one.return_value = {"id": 1, "name": "test_project"}
    mock_controller.get_endpoint.return_value = Mock(status=200)
    # create_or_update_if_needed returns a result dict
    mock_controller.create_or_update_if_needed.return_value = {
        "changed": False,
        "id": 1,
    }
    mock_controller.create.return_value = {"changed": True}

    with patch(
        "ansible_collections.ansible.eda.plugins.modules.project.Controller",
        return_value=mock_controller,
    ):
        with patch("ansible_collections.ansible.eda.plugins.modules.project.Client"):
            with patch(
                "ansible_collections.ansible.eda.plugins.modules.project.lookup_resource_id",
                return_value=1,
            ):
                with patch(
                    "ansible_collections.ansible.eda.plugins.modules.project.AnsibleModule",
                    return_value=mock_module,
                ):
                    project.main()

                    # Verify create was called for sync
                    assert mock_controller.create.called
                    assert mock_module.exit_json.called


def test_wait_for_project_sync_completed() -> None:
    """Test wait_for_project_sync when import completes successfully."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = {"import_state": "completed"}
    mock_controller.get_endpoint.return_value = mock_response

    # Should complete without raising
    with patch("time.sleep"):  # Skip actual sleep
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    assert mock_controller.get_endpoint.called


def test_wait_for_project_sync_failed() -> None:
    """Test wait_for_project_sync when import fails."""
    from ansible_collections.ansible.eda.plugins.module_utils.errors import EDAError
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = {
        "import_state": "failed",
        "import_error": "Repository not found",
    }
    mock_controller.get_endpoint.return_value = mock_response

    with pytest.raises(EDAError) as exc_info:
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    assert "Project import failed" in str(exc_info.value)
    assert "Repository not found" in str(exc_info.value)


def test_wait_for_project_sync_timeout() -> None:
    """Test wait_for_project_sync when it times out."""
    from ansible_collections.ansible.eda.plugins.module_utils.errors import EDAError
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = {"import_state": "pending"}
    mock_controller.get_endpoint.return_value = mock_response

    with patch("time.sleep"):  # Skip actual sleep
        with patch("time.time") as mock_time:
            # Simulate timeout by making time progress
            mock_time.side_effect = [0, 0, 5, 11]  # Start, check, check, timeout

            with pytest.raises(EDAError) as exc_info:
                project.wait_for_project_sync(
                    mock_controller, project_id=1, timeout=10, poll_interval=1
                )

    assert "Timeout waiting for project import" in str(exc_info.value)
    assert "Last state: pending" in str(exc_info.value)


def test_wait_for_project_sync_state_transitions() -> None:
    """Test wait_for_project_sync with state transitions."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()

    # Simulate state transitions: pending -> running -> completed
    responses = [
        Mock(status=200, json={"import_state": "pending"}),
        Mock(status=200, json={"import_state": "running"}),
        Mock(status=200, json={"import_state": "completed"}),
    ]
    mock_controller.get_endpoint.side_effect = responses

    with patch("time.sleep"):  # Skip actual sleep
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    # Should have called get_endpoint 3 times
    assert mock_controller.get_endpoint.call_count == 3


def test_wait_for_project_sync_transient_errors() -> None:
    """Test wait_for_project_sync handles transient errors."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()

    # Simulate transient error then success using side_effect list
    mock_controller.get_endpoint.side_effect = [
        ConnectionError("Temporary network issue"),
        Mock(status=200, json={"import_state": "completed"}),
    ]

    with patch("time.sleep"):  # Skip actual sleep
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    # Should have retried after error
    assert mock_controller.get_endpoint.call_count == 2


def test_wait_for_project_sync_eda_error_not_caught() -> None:
    """Test wait_for_project_sync re-raises EDAError."""
    from ansible_collections.ansible.eda.plugins.module_utils.errors import EDAError
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()
    mock_controller.get_endpoint.side_effect = EDAError("API error")

    with pytest.raises(EDAError) as exc_info:
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    assert "API error" in str(exc_info.value)


def test_wait_for_project_sync_no_json() -> None:
    """Test wait_for_project_sync when response has no json."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()

    # First response has no json, second has completed
    responses = [
        Mock(status=200, json=None),
        Mock(status=200, json={"import_state": "completed"}),
    ]
    mock_controller.get_endpoint.side_effect = responses

    with patch("time.sleep"):  # Skip actual sleep
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    assert mock_controller.get_endpoint.call_count == 2


def test_wait_for_project_sync_non_200_status() -> None:
    """Test wait_for_project_sync when status is not 200."""
    from ansible_collections.ansible.eda.plugins.modules import project

    mock_controller = Mock()

    # First response is 404, second is 200 with completed
    responses = [
        Mock(status=404, json=None),
        Mock(status=200, json={"import_state": "completed"}),
    ]
    mock_controller.get_endpoint.side_effect = responses

    with patch("time.sleep"):  # Skip actual sleep
        project.wait_for_project_sync(mock_controller, project_id=1, timeout=10)

    assert mock_controller.get_endpoint.call_count == 2
