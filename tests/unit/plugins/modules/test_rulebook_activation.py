from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from plugins.modules.rulebook_activation import (
    create_params,
    find_matching_source,
    process_event_streams,
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
        mock_module.fail_json.side_effect = Exception("fail")

        with (
            patch(
                "plugins.modules.rulebook_activation.lookup_resource_id",
                return_value=None,
            ),
            pytest.raises(Exception, match="fail"),
        ):
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

    def test_awx_token_re_resolved_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """User-provided awx_token_name should be resolved via lookup on update."""
        existing_activation["awx_token_id"] = 99
        mock_module.params["awx_token_name"] = "my-new-token"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=42,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=existing_activation,
            )

        assert result["awx_token_id"] == 42

    def test_awx_token_not_updated_when_lookup_returns_none(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """When awx_token lookup returns None, existing value should be preserved."""
        existing_activation["awx_token_id"] = 99
        mock_module.params["awx_token_name"] = "bad-token"

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=None,
        ):
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=existing_activation,
            )

        assert result["awx_token_id"] == 99

    def test_awx_token_not_looked_up_when_not_provided(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """When awx_token_name is not set, no lookup should occur."""
        existing_activation["awx_token_id"] = 99
        mock_module.params["awx_token_name"] = None

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
        ) as mock_lookup:
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=False,
                existing=existing_activation,
            )

        mock_lookup.assert_not_called()
        assert result["awx_token_id"] == 99

    def test_k8s_service_name_re_resolved_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """User-provided k8s_service_name should override existing value on update."""
        existing_activation["k8s_service_name"] = "old-service"
        mock_module.params["k8s_service_name"] = "new-service"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["k8s_service_name"] == "new-service"

    def test_k8s_service_name_skipped_on_aap_24(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """k8s_service_name should not be re-resolved when is_aap_24=True."""
        existing_activation["k8s_service_name"] = "old-service"
        mock_module.params["k8s_service_name"] = "new-service"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=True,
            existing=existing_activation,
        )

        assert result["k8s_service_name"] == "old-service"

    def test_k8s_service_name_preserved_when_not_provided(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """When k8s_service_name is not set, existing value should be preserved."""
        existing_activation["k8s_service_name"] = "existing-service"
        mock_module.params["k8s_service_name"] = None

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["k8s_service_name"] == "existing-service"

    def test_credentials_skipped_on_aap_24(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """eda_credentials should not be re-resolved when is_aap_24=True."""
        existing_activation["eda_credentials"] = [1, 2]
        mock_module.params["eda_credentials"] = ["cred-one", "cred-two"]

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
        ) as mock_lookup:
            result = create_params(
                mock_module,
                mock_controller,
                is_aap_24=True,
                existing=existing_activation,
            )

        mock_lookup.assert_not_called()
        assert result["eda_credentials"] == [1, 2]

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

    def test_is_enabled_preserved_for_present_state_on_existing(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        existing_activation: Dict[str, Any],
    ) -> None:
        """state=present on existing should preserve the existing is_enabled value."""
        mock_module.params["state"] = "present"

        result = create_params(
            mock_module,
            mock_controller,
            is_aap_24=False,
            existing=existing_activation,
        )

        assert result["is_enabled"] is False

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


class TestFindMatchingSource:
    """Tests for find_matching_source."""

    def test_returns_matching_source(self) -> None:
        """Should return the source whose name matches the event's source_name."""
        sources = [
            {"name": "source-a", "rulebook_hash": "aaa"},
            {"name": "source-b", "rulebook_hash": "bbb"},
        ]
        event = {"source_name": "source-b"}
        result = find_matching_source(event, sources, Mock())
        assert result["name"] == "source-b"
        assert result["rulebook_hash"] == "bbb"

    def test_fails_when_no_match(self) -> None:
        """Should call fail_json when no source matches."""
        sources = [{"name": "source-a", "rulebook_hash": "aaa"}]
        event = {"source_name": "nonexistent"}
        module = Mock()
        find_matching_source(event, sources, module)
        module.fail_json.assert_called_once()
        assert "nonexistent" in module.fail_json.call_args[1]["msg"]


class TestProcessEventStreams:
    """Tests for process_event_streams."""

    @pytest.fixture
    def mock_sources(self) -> List[Dict[str, Any]]:
        return [
            {"name": "source-0", "rulebook_hash": "hash0"},
            {"name": "source-1", "rulebook_hash": "hash1"},
        ]

    def test_happy_path_with_source_index(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should resolve source by index and look up event stream."""
        mock_module.params["event_streams"] = [
            {"event_stream": "my-stream", "source_index": 0, "source_name": None}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=42,
        ):
            result = process_event_streams(1, mock_controller, mock_module)

        assert len(result) == 1
        assert result[0]["source_name"] == "source-0"
        assert result[0]["rulebook_hash"] == "hash0"
        assert result[0]["event_stream_name"] == "my-stream"
        assert result[0]["event_stream_id"] == 42

    def test_happy_path_with_source_name(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should resolve source by name and look up event stream."""
        mock_module.params["event_streams"] = [
            {
                "event_stream": "my-stream",
                "source_index": None,
                "source_name": "source-1",
            }
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=99,
        ):
            result = process_event_streams(1, mock_controller, mock_module)

        assert len(result) == 1
        assert result[0]["source_name"] == "source-1"
        assert result[0]["rulebook_hash"] == "hash1"
        assert result[0]["event_stream_id"] == 99

    def test_error_both_source_index_and_source_name(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when both source_index and source_name are provided."""
        mock_module.params["event_streams"] = [
            {"event_stream": "my-stream", "source_index": 1, "source_name": "source-0"}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert "mutually exclusive" in mock_module.fail_json.call_args[1]["msg"]

    def test_error_neither_source_index_nor_source_name(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when neither source_index nor source_name is provided."""
        mock_module.params["event_streams"] = [
            {"event_stream": "my-stream", "source_index": None, "source_name": None}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert "must specify one" in mock_module.fail_json.call_args[1]["msg"]

    def test_error_source_index_out_of_range(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when source_index is out of range."""
        mock_module.params["event_streams"] = [
            {"event_stream": "my-stream", "source_index": 99, "source_name": None}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert "out of range" in mock_module.fail_json.call_args[1]["msg"]

    def test_error_no_event_stream_name(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when event_stream is None."""
        mock_module.params["event_streams"] = [
            {"event_stream": None, "source_index": 0, "source_name": None}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert (
            "must specify an event stream" in mock_module.fail_json.call_args[1]["msg"]
        )

    def test_error_event_stream_not_found(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when event stream lookup returns None."""
        mock_module.params["event_streams"] = [
            {"event_stream": "missing-stream", "source_index": 0, "source_name": None}
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            return_value=None,
        ):
            process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert "does not exist" in mock_module.fail_json.call_args[1]["msg"]

    def test_error_controller_fails_to_get_sources(
        self, mock_module: Mock, mock_controller: Mock
    ) -> None:
        """Should fail when controller raises EDAError getting sources."""
        from plugins.module_utils.errors import EDAError

        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_module.params["event_streams"] = []
        mock_controller.get_one_or_many.side_effect = EDAError("connection refused")
        mock_module.fail_json.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert (
            "Failed to get rulebook source list"
            in mock_module.fail_json.call_args[1]["msg"]
        )

    def test_find_matching_source_not_found_via_process(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should fail when source_name doesn't match any source."""
        mock_module.params["event_streams"] = [
            {
                "event_stream": "my-stream",
                "source_index": None,
                "source_name": "nonexistent",
            }
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        process_event_streams(1, mock_controller, mock_module)

        mock_module.fail_json.assert_called_once()
        assert "nonexistent" in mock_module.fail_json.call_args[1]["msg"]

    def test_multiple_event_streams(
        self,
        mock_module: Mock,
        mock_controller: Mock,
        mock_sources: List[Dict[str, Any]],
    ) -> None:
        """Should process multiple event streams in one call."""
        mock_module.params["event_streams"] = [
            {"event_stream": "stream-a", "source_index": 0, "source_name": None},
            {"event_stream": "stream-b", "source_index": 1, "source_name": None},
        ]
        mock_module.params["rulebook_name"] = "test-rulebook"
        mock_controller.get_one_or_many.return_value = mock_sources

        with patch(
            "plugins.modules.rulebook_activation.lookup_resource_id",
            side_effect=[10, 20],
        ):
            result = process_event_streams(1, mock_controller, mock_module)

        assert len(result) == 2
        assert result[0]["event_stream_id"] == 10
        assert result[1]["event_stream_id"] == 20


class TestMainStateTransition:
    """Tests for state transition and create_or_update logic in main()."""

    @pytest.fixture
    def module_params(self) -> Dict[str, Any]:
        return {
            "name": "test-activation",
            "new_name": None,
            "description": "test",
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
            "state": "enabled",
            "restart_on_project_update": False,
            "update_secrets": True,
            "controller_host": "http://localhost",
            "controller_username": "admin",
            "controller_password": "password",
            "controller_token": None,
            "request_timeout": 10.0,
            "validate_certs": False,
        }

    @pytest.fixture
    def existing_disabled_activation(self) -> Dict[str, Any]:
        return {
            "id": 1,
            "name": "test-activation",
            "description": "test",
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

    @pytest.fixture
    def existing_enabled_activation(self) -> Dict[str, Any]:
        return {
            "id": 1,
            "name": "test-activation",
            "description": "test",
            "extra_var": "",
            "restart_policy": "on-failure",
            "is_enabled": True,
            "log_level": "error",
            "decision_environment_id": 1,
            "rulebook_id": 1,
            "organization_id": 1,
            "eda_credentials": [],
            "restart_on_project_update": False,
            "enable_persistence": False,
        }

    def _run_main(
        self,
        module_params: Dict[str, Any],
        existing_activation: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], MagicMock]:
        """Helper to run main() with mocked dependencies."""
        from plugins.modules import rulebook_activation

        mock_module = MagicMock()
        mock_module.params = module_params
        mock_module.check_mode = False

        mock_controller = MagicMock()
        mock_config_response = MagicMock()
        mock_config_response.status = 200
        mock_controller.get_endpoint.return_value = mock_config_response
        mock_controller.get_exactly_one.return_value = existing_activation
        mock_controller.get_item_name.return_value = existing_activation["name"]
        mock_controller.create_or_update_if_needed.return_value = {"changed": False}

        captured_exit: Dict[str, Any] = {}

        def capture_exit(**kwargs: Any) -> None:
            captured_exit.update(kwargs)
            raise SystemExit(0)

        mock_module.exit_json.side_effect = capture_exit

        with (
            patch.object(
                rulebook_activation, "AnsibleModule", return_value=mock_module
            ),
            patch.object(rulebook_activation, "Client"),
            patch.object(
                rulebook_activation, "Controller", return_value=mock_controller
            ),
            patch.object(rulebook_activation, "HAS_YAML", True),
        ):
            with pytest.raises(SystemExit):
                rulebook_activation.main()

        return captured_exit, mock_controller

    def test_state_transition_disabled_to_enabled(
        self,
        module_params: Dict[str, Any],
        existing_disabled_activation: Dict[str, Any],
    ) -> None:
        """Enabling a disabled activation should post to enable endpoint and exit early."""
        module_params["state"] = "enabled"

        result, controller = self._run_main(module_params, existing_disabled_activation)

        controller.post_endpoint.assert_called_once_with(
            endpoint="activations/1/enable"
        )
        controller.create_or_update_if_needed.assert_not_called()
        assert result["changed"] is True

    def test_state_transition_enabled_to_disabled(
        self, module_params: Dict[str, Any], existing_enabled_activation: Dict[str, Any]
    ) -> None:
        """Disabling an enabled activation should post to disable endpoint and exit early."""
        module_params["state"] = "disabled"

        result, controller = self._run_main(module_params, existing_enabled_activation)

        controller.post_endpoint.assert_called_once_with(
            endpoint="activations/1/disable"
        )
        controller.create_or_update_if_needed.assert_not_called()
        assert result["changed"] is True

    def test_no_state_transition_already_enabled(
        self, module_params: Dict[str, Any], existing_enabled_activation: Dict[str, Any]
    ) -> None:
        """When activation is already enabled and state=enabled, still run param update."""
        module_params["state"] = "enabled"

        result, controller = self._run_main(module_params, existing_enabled_activation)

        controller.post_endpoint.assert_not_called()
        controller.create_or_update_if_needed.assert_called_once()
        assert result["changed"] is False

    def test_no_state_transition_already_disabled(
        self,
        module_params: Dict[str, Any],
        existing_disabled_activation: Dict[str, Any],
    ) -> None:
        """When activation is already disabled and state=disabled, still run param update."""
        module_params["state"] = "disabled"

        result, controller = self._run_main(module_params, existing_disabled_activation)

        controller.post_endpoint.assert_not_called()
        controller.create_or_update_if_needed.assert_called_once()
        assert result["changed"] is False

    def test_create_params_called_with_existing(
        self,
        module_params: Dict[str, Any],
        existing_disabled_activation: Dict[str, Any],
    ) -> None:
        """create_params should be called with existing activation data for state=present."""
        module_params["state"] = "present"

        with patch(
            "plugins.modules.rulebook_activation.create_params",
            return_value={"name": "test-activation"},
        ) as mock_create_params:
            result, controller = self._run_main(
                module_params, existing_disabled_activation
            )

            mock_create_params.assert_called_once()
            call_args = mock_create_params.call_args
            existing_arg = (
                call_args[1].get("existing")
                if call_args[1]
                else call_args[0][3] if len(call_args[0]) > 3 else None
            )
            assert existing_arg is not None

    def test_update_with_new_name(
        self, module_params: Dict[str, Any], existing_enabled_activation: Dict[str, Any]
    ) -> None:
        """When new_name is provided, it should be used in activation_params."""
        module_params["state"] = "present"
        module_params["new_name"] = "renamed-activation"

        result, controller = self._run_main(module_params, existing_enabled_activation)

        call_args = controller.create_or_update_if_needed.call_args
        activation_params = call_args[0][1]
        assert activation_params["name"] == "renamed-activation"
