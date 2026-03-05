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
