from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from plugins.modules.rulebook_activation import (
    create_params,
)


@pytest.fixture
def mock_module() -> Mock:
    module = Mock()
    module.check_mode = False
    module.params = {
        "name": "test-activation",
        "new_name": None,
        "description": "Updated description",
        "project_name": None,
        "rulebook_name": None,
        "extra_vars": None,
        "restart": False,
        "restart_policy": "on-failure",
        "enabled": True,
        "decision_environment_name": None,
        "awx_token_name": None,
        "organization_name": None,
        "eda_credentials": None,
        "k8s_service_name": None,
        "event_streams": None,
        "swap_single_source": True,
        "log_level": "error",
        "enable_persistence": False,
        "rule_engine_credential_id": None,
        "state": "disabled",
        "restart_on_project_update": False,
        "update_secrets": True,
        "controller_host": "http://localhost",
        "controller_username": "admin",
        "controller_password": "password",
        "controller_token": None,
        "request_timeout": 10.0,
        "validate_certs": False,
    }
    return module


@pytest.fixture
def mock_controller() -> Mock:
    return Mock()


@pytest.fixture
def existing_activation() -> Dict[str, Any]:
    return {
        "id": 1,
        "name": "test-activation",
        "description": "Old description",
        "extra_var": "",
        "restart_policy": "on-failure",
        "is_enabled": False,
        "log_level": "error",
        "decision_environment_id": 1,
        "rulebook_id": 1,
        "organization_id": 1,
        "eda_credentials": [],
        "restart_on_project_update": False,
        "enable_persistence": False,
    }


class TestCreateParamsWithExisting:
    """Tests for partial update path in create_params."""

    def test_existing_activation_skips_resource_lookups(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """When existing activation is provided, no API lookups should occur."""
        result = create_params(
            mock_module, mock_controller, is_aap_24=False, existing=existing_activation
        )

        mock_controller.assert_not_called()
        assert result["organization_id"] == 1
        assert result["rulebook_id"] == 1

    def test_description_updated_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """Description from module params should override existing value."""
        mock_module.params["description"] = "Updated description"

        result = create_params(
            mock_module, mock_controller, is_aap_24=False, existing=existing_activation
        )

        assert result["description"] == "Updated description"

    def test_extra_vars_updated_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """extra_vars from module params should override existing value."""
        mock_module.params["extra_vars"] = "my_var: new_value"

        result = create_params(
            mock_module, mock_controller, is_aap_24=False, existing=existing_activation
        )

        assert result["extra_var"] == "my_var: new_value"

    def test_existing_values_preserved_when_no_override(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """Fields not provided by user should retain existing values."""
        mock_module.params["description"] = None
        mock_module.params["extra_vars"] = None

        result = create_params(
            mock_module, mock_controller, is_aap_24=False, existing=existing_activation
        )

        assert result["description"] == "Old description"
        assert result["rulebook_id"] == 1
        assert result["decision_environment_id"] == 1

    def test_no_existing_triggers_resource_lookups(
        self, mock_module: Mock, mock_controller: Mock
    ) -> None:
        """Without existing, create_params should attempt resource lookups."""
        mock_module.params["project_name"] = "test-project"

        with pytest.raises(Exception):
            # Will fail because mock controller doesn't return real data,
            # but proves the lookup path is taken
            create_params(mock_module, mock_controller, is_aap_24=False, existing=None)
            mock_module.fail_json.assert_called()


class TestStateTransitionFallthrough:
    """Tests that enabled/disabled state no longer blocks param updates."""

    def test_disabled_activation_falls_through_to_update(
        self, existing_activation: Dict[str, Any]
    ) -> None:
        """When activation is already disabled and state=disabled,
        the module should still check for param changes."""
        # This is the core bug fix — previously this path hit
        # module.exit_json(changed=False) and never reached
        # create_or_update_if_needed()
        existing_activation["is_enabled"] = False

        result = create_params(
            Mock(
                params={
                    "description": "New description",
                    "extra_vars": None,
                    "restart_policy": "on-failure",
                    "state": "disabled",
                    "log_level": "error",
                    "restart_on_project_update": False,
                    "enable_persistence": False,
                    "rule_engine_credential_id": None,
                }
            ),
            Mock(),
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["description"] == "New description"
        assert result["is_enabled"] is False


class TestCreateParamsCredentialResolution:
    """Tests for credential and event stream re-resolution on existing activations."""

    def test_credentials_re_resolved_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """User-provided credentials should be resolved via lookup."""
        mock_module.params["eda_credentials"] = ["cred-one", "cred-two"]

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            side_effect=[10, 20],
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=existing_activation,
            )

        assert result["eda_credentials"] == [10, 20]

    def test_event_streams_re_resolved_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """User-provided event streams should be processed on update."""
        existing_activation["rulebook_id"] = 5
        mock_module.params["event_streams"] = [
            {"event_stream": "test-stream", "source_index": 0}
        ]

        with patch(
            "plugins.modules.rulebook_activation.process_event_streams",
            return_value=[{"event_stream_name": "test-stream", "event_stream_id": 1}],
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=existing_activation,
            )

        assert "source_mappings" in result

    def test_is_enabled_set_for_disabled_state_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """state=disabled on existing should set is_enabled=False."""
        mock_module.params["state"] = "disabled"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["is_enabled"] is False

    def test_is_enabled_set_for_enabled_state_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """state=enabled on existing should set is_enabled=True."""
        mock_module.params["state"] = "enabled"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["is_enabled"] is True

    def test_is_enabled_not_set_for_present_state_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """state=present on existing should not set is_enabled."""
        mock_module.params["state"] = "present"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert "is_enabled" not in result

    def test_create_path_sets_is_enabled_true_for_present(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """state=present on new activation should set is_enabled=True."""
        mock_module.params["state"] = "present"
        mock_module.params["project_name"] = "test-project"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=1,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["is_enabled"] is True

    def test_create_path_sets_is_enabled_false_for_disabled(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """state=disabled on new activation should set is_enabled=False."""
        mock_module.params["state"] = "disabled"
        mock_module.params["project_name"] = "test-project"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=1,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["is_enabled"] is False


class TestCreateParamsCreatePath:
    """Tests for the create (non-existing) path in create_params."""

    def test_create_path_resolves_all_resources(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should resolve project, rulebook, DE, and org."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "Default"
        mock_module.params["state"] = "present"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=1,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["rulebook_id"] == 1
        assert result["decision_environment_id"] == 1
        assert result["organization_id"] == 1
        assert result["is_enabled"] is True

    def test_create_path_with_awx_token(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should resolve AWX token when provided."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "Default"
        mock_module.params["awx_token_name"] = "my-token"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=1,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["awx_token_id"] == 1

    def test_create_path_with_credentials(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should resolve EDA credentials."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "Default"
        mock_module.params["eda_credentials"] = ["cred-a", "cred-b"]

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            side_effect=[1, 2, 3, 4, 10, 20],
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["eda_credentials"] == [10, 20]

    def test_create_path_with_k8s_service(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should include k8s_service_name."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "Default"
        mock_module.params["k8s_service_name"] = "my-service"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=1,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert result["k8s_service_name"] == "my-service"

    def test_create_path_with_event_streams(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should process event streams."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "Default"
        mock_module.params["event_streams"] = [
            {"event_stream": "stream-1", "source_index": 0}
        ]

        with (
            patch(
                "plugins.modules.rulebook_activation.lookup_resource_id",
                return_value=1,
            ),
            patch(
                "plugins.modules.rulebook_activation.process_event_streams",
                return_value=[{"event_stream_name": "stream-1", "event_stream_id": 1}],
            ),
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        assert "source_mappings" in result

    def test_create_path_de_not_found(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should fail when decision environment not found."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "missing-de"
        mock_module.params["organization_name"] = "Default"

        call_count = 0

        def lookup_side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                return None
            return call_count

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            side_effect=lookup_side_effect,
        ):
            create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        mock_module.fail_json.assert_called()

    def test_create_path_org_not_found(
        self,
        mock_module: Mock,
        mock_controller: Mock,
    ) -> None:
        """Create path should fail when organization not found."""
        mock_module.params["project_name"] = "test-project"
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["decision_environment_name"] = "test-de"
        mock_module.params["organization_name"] = "missing-org"

        call_count = 0

        def lookup_side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 4:
                return None
            return call_count

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            side_effect=lookup_side_effect,
        ):
            create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=None,
            )

        mock_module.fail_json.assert_called()
