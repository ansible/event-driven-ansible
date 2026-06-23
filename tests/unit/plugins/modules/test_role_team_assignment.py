# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Callable, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

MODULE_PATH = "ansible_collections.ansible.eda.plugins.modules.role_team_assignment"


class _AnsibleExit(Exception):
    """Simulates module.exit_json / module.fail_json halting execution."""


def _make_module(params_override: Optional[dict[str, Any]] = None) -> MagicMock:
    """Build a mock AnsibleModule with sensible defaults."""
    params: dict[str, Any] = {
        "controller_host": "https://eda.example.com",
        "controller_username": "admin",
        "controller_password": "password",
        "controller_token": None,
        "request_timeout": 10.0,
        "validate_certs": True,
        "role_definition": "Organization Auditor",
        "team": "test-team",
        "team_ansible_id": None,
        "object_id": 1,
        "object_ansible_id": None,
        "state": "present",
    }
    if params_override:
        params.update(params_override)

    module = MagicMock()
    module.params = params
    module.check_mode = False
    module.exit_json.side_effect = _AnsibleExit
    module.fail_json.side_effect = _AnsibleExit
    return module


def _make_assignment(
    assignment_id: int = 1,
    role_def_id: int = 6,
    team_id: int = 1,
    object_id: Optional[str] = "1",
) -> dict[str, Any]:
    return {
        "id": assignment_id,
        "role_definition": role_def_id,
        "team": team_id,
        "object_id": object_id,
        "content_type": "shared.organization",
    }


def _make_api_list(assignments: list[dict[str, Any]]) -> Mock:
    """Wrap assignments in a paginated API response."""
    return Mock(
        status=200,
        json={"count": len(assignments), "results": assignments},
    )


def _resolve_response(
    resource_id: int,
    name: str,
    extra: Optional[dict[str, Any]] = None,
) -> Mock:
    """Build a paginated GET response for name-based ID resolution."""
    item: dict[str, Any] = {"id": resource_id, "name": name}
    if extra:
        item.update(extra)
    return Mock(
        status=200,
        json={"count": 1, "results": [item]},
    )


def _setup_main(
    params_override: Optional[dict[str, Any]],
    get_responses: list[Mock],
    post_response: Optional[Mock] = None,
    delete_response: Optional[Mock] = None,
    check_mode: bool = False,
) -> tuple[MagicMock, MagicMock]:
    """Wire up mocks for a main() test and return (module, mock_client)."""
    module = _make_module(params_override)
    module.check_mode = check_mode

    mock_client = MagicMock()
    mock_client.get.side_effect = list(get_responses)
    if post_response:
        mock_client.post.return_value = post_response
    if delete_response:
        mock_client.delete.return_value = delete_response

    return module, mock_client


def _run_main(module: MagicMock, mock_client: MagicMock) -> None:
    """Run main() with the given module and client mocks."""
    from ansible_collections.ansible.eda.plugins.modules.role_team_assignment import (  # type: ignore
        main,
    )

    with (
        patch(f"{MODULE_PATH}.AnsibleModule", return_value=module),
        patch(f"{MODULE_PATH}.Client", return_value=mock_client),
        pytest.raises(_AnsibleExit),
    ):
        main()


# ---------------------------------------------------------------------------
# _find_existing — tests the real function with a mock controller
# ---------------------------------------------------------------------------
class TestFindExisting:
    @staticmethod
    def _import() -> Callable[..., Any]:
        from ansible_collections.ansible.eda.plugins.modules.role_team_assignment import (
            _find_existing,
        )

        return _find_existing  # type: ignore[no-any-return]

    def test_found_by_object_id(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = _make_api_list([_make_assignment()])
        result = fn(ctrl, {"role_definition": 6, "team": 1}, 1)
        assert result is not None
        assert result["id"] == 1
        ctrl.get_endpoint.assert_called_once_with(
            "role_team_assignments",
            data={"role_definition": 6, "team": 1, "page_size": 200},
        )

    def test_not_found_empty_results(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = _make_api_list([])
        assert fn(ctrl, {"role_definition": 6, "team": 1}, 1) is None

    def test_null_object_id_matches_null(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = _make_api_list(
            [_make_assignment(object_id=None)]
        )
        result = fn(ctrl, {"role_definition": 6, "team": 1}, None)
        assert result is not None

    def test_object_id_mismatch_returns_none(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = _make_api_list(
            [_make_assignment(object_id="99")]
        )
        assert fn(ctrl, {"role_definition": 6, "team": 1}, 1) is None

    def test_string_int_comparison(self) -> None:
        """API returns object_id as '1' (str), user passes 1 (int)."""
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = _make_api_list(
            [_make_assignment(object_id="1")]
        )
        assert fn(ctrl, {"role_definition": 6, "team": 1}, 1) is not None

    def test_matches_by_object_ansible_id(self) -> None:
        """When object_ansible_id is provided, match on it instead of object_id."""
        fn = self._import()
        ctrl = MagicMock()
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assignment = _make_assignment()
        assignment["object_ansible_id"] = uuid
        ctrl.get_endpoint.return_value = _make_api_list([assignment])
        result = fn(
            ctrl, {"role_definition": 6, "team": 1}, None, object_ansible_id=uuid
        )
        assert result is not None
        assert result["id"] == 1

    def test_object_ansible_id_mismatch(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        assignment = _make_assignment()
        assignment["object_ansible_id"] = "aaaa-bbbb"
        ctrl.get_endpoint.return_value = _make_api_list([assignment])
        result = fn(
            ctrl, {"role_definition": 6, "team": 1}, None, object_ansible_id="cccc-dddd"
        )
        assert result is None

    def test_api_error_returns_none(self) -> None:
        fn = self._import()
        ctrl = MagicMock()
        ctrl.get_endpoint.return_value = Mock(status=500)
        assert fn(ctrl, {"role_definition": 6, "team": 1}, 1) is None


# ---------------------------------------------------------------------------
# _resolve_id — tests the real function
# ---------------------------------------------------------------------------
class TestResolveId:
    @staticmethod
    def _import() -> Callable[..., Any]:
        from ansible_collections.ansible.eda.plugins.modules.role_team_assignment import (
            _resolve_id,
        )

        return _resolve_id  # type: ignore[no-any-return]

    def test_numeric_string_returns_int_without_api_call(self) -> None:
        fn = self._import()
        module = MagicMock()
        ctrl = MagicMock()
        assert fn(module, ctrl, "role_definitions", "42", "Role") == 42

    def test_name_resolves_via_lookup(self) -> None:
        fn = self._import()
        module = MagicMock()
        ctrl = MagicMock()
        with patch(f"{MODULE_PATH}.lookup_resource_id", return_value=6) as mock_lookup:
            result = fn(module, ctrl, "role_definitions", "Org Auditor", "Role")
        assert result == 6
        mock_lookup.assert_called_once_with(
            module,
            ctrl,
            "role_definitions",
            "Org Auditor",
        )

    def test_name_not_found_calls_fail_json(self) -> None:
        fn = self._import()
        module = MagicMock()
        module.fail_json.side_effect = _AnsibleExit
        ctrl = MagicMock()
        with (
            patch(f"{MODULE_PATH}.lookup_resource_id", return_value=None),
            pytest.raises(_AnsibleExit),
        ):
            fn(module, ctrl, "role_definitions", "nope", "Role definition")
        assert "not found" in module.fail_json.call_args[1]["msg"]
        assert "'nope'" in module.fail_json.call_args[1]["msg"]


# ---------------------------------------------------------------------------
# main() tests — only Client and AnsibleModule are patched.
# _resolve_id and _find_existing run for real against mock HTTP responses.
# This verifies payloads, filter construction, and endpoint paths.
# ---------------------------------------------------------------------------
class TestMainPresent:
    def test_creates_with_correct_payload(self) -> None:
        """Verifies the POST payload has role_definition, team, object_id."""
        module, client = _setup_main(
            params_override={},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
            post_response=Mock(status=201, json={"id": 42}),
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=True, id=42)
        post_call = client.post.call_args
        payload = (
            post_call[1].get("data") or post_call[0][1]
            if len(post_call[0]) > 1
            else post_call[1]["data"]
        )
        assert payload["role_definition"] == 6
        assert payload["team"] == 1
        assert payload["object_id"] == 1

    def test_idempotent_when_exists(self) -> None:
        module, client = _setup_main(
            params_override={},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([_make_assignment()]),
            ],
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=False, id=1)
        client.post.assert_not_called()

    def test_check_mode_does_not_post(self) -> None:
        module, client = _setup_main(
            params_override={},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
            check_mode=True,
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=True)
        client.post.assert_not_called()

    def test_team_ansible_id_payload(self) -> None:
        """Verifies team_ansible_id is sent in payload and filter, not team."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        module, client = _setup_main(
            params_override={
                "team": None,
                "team_ansible_id": uuid,
            },
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _make_api_list([]),
            ],
            post_response=Mock(status=201, json={"id": 99}),
        )
        _run_main(module, client)

        post_data = client.post.call_args[1].get("data", {})
        assert "team" not in post_data
        assert post_data["team_ansible_id"] == uuid

        find_call = client.get.call_args_list[-1]
        filter_data = find_call[1].get("data", {})
        assert filter_data.get("team_ansible_id") == uuid

    def test_object_ansible_id_payload(self) -> None:
        """Verifies object_ansible_id is sent instead of object_id."""
        obj_uuid = "660e8400-e29b-41d4-a716-446655440000"
        module, client = _setup_main(
            params_override={
                "object_id": None,
                "object_ansible_id": obj_uuid,
            },
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
            post_response=Mock(status=201, json={"id": 77}),
        )
        _run_main(module, client)

        post_data = client.post.call_args[1].get("data", {})
        assert "object_id" not in post_data
        assert post_data["object_ansible_id"] == obj_uuid

        # Verify filter used object_ansible_id for the find call
        find_call = client.get.call_args_list[-1]
        filter_data = find_call[1].get("data", {})
        assert filter_data.get("object_ansible_id") == obj_uuid

    def test_post_failure_calls_fail_json(self) -> None:
        module, client = _setup_main(
            params_override={},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
            post_response=Mock(
                status=400,
                data='{"detail":"bad request"}',
                json={"detail": "bad request"},
            ),
        )
        _run_main(module, client)

        module.fail_json.assert_called_once()
        assert "HTTP error" in module.fail_json.call_args[1]["msg"]


class TestMainAbsent:
    def test_deletes_with_correct_endpoint(self) -> None:
        module, client = _setup_main(
            params_override={"state": "absent"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([_make_assignment(assignment_id=55)]),
            ],
            delete_response=Mock(status=204),
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=True, id=55)
        assert "55" in str(client.delete.call_args)

    def test_idempotent_when_not_exists(self) -> None:
        module, client = _setup_main(
            params_override={"state": "absent"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=False)
        client.delete.assert_not_called()

    def test_check_mode_does_not_delete(self) -> None:
        module, client = _setup_main(
            params_override={"state": "absent"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([_make_assignment()]),
            ],
            check_mode=True,
        )
        _run_main(module, client)

        module.exit_json.assert_called_once_with(changed=True, id=1)
        client.delete.assert_not_called()

    def test_delete_failure_calls_fail_json(self) -> None:
        module, client = _setup_main(
            params_override={"state": "absent"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([_make_assignment()]),
            ],
            delete_response=Mock(status=500, data="internal error"),
        )
        _run_main(module, client)

        module.fail_json.assert_called_once()
        assert "HTTP error" in module.fail_json.call_args[1]["msg"]


class TestMainExists:
    def test_returns_details_when_found(self) -> None:
        module, client = _setup_main(
            params_override={"state": "exists"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([_make_assignment()]),
            ],
        )
        _run_main(module, client)

        kwargs = module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert kwargs["id"] == 1
        assert kwargs["content_type"] == "shared.organization"

    def test_returns_not_found(self) -> None:
        module, client = _setup_main(
            params_override={"state": "exists"},
            get_responses=[
                _resolve_response(6, "Organization Auditor"),
                _resolve_response(1, "test-team"),
                _make_api_list([]),
            ],
        )
        _run_main(module, client)

        kwargs = module.exit_json.call_args[1]
        assert kwargs["changed"] is False
        assert "not found" in kwargs["msg"]


class TestMainEdaError:
    def test_eda_error_calls_fail_json(self) -> None:
        """Verifies the except EDAError handler."""
        from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
            EDAHTTPError,
        )

        module, client = _setup_main(
            params_override={},
            get_responses=[],
        )
        client.get.side_effect = EDAHTTPError("connection refused")

        _run_main(module, client)

        module.fail_json.assert_called_once()
        assert "connection refused" in module.fail_json.call_args[1]["msg"]
