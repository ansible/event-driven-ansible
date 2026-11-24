# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAHTTPError,
)
from ansible_collections.ansible.eda.plugins.modules.rulebook_activation import (  # type: ignore
    create_params,
    extra_vars_are_equal,
    format_extra_vars,
    main,
)

MODULE_PATH = "ansible_collections.ansible.eda.plugins.modules.rulebook_activation"

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


@pytest.mark.parametrize(
    "old, new",
    [
        ("alpha: 1\nzeta: 2\n", "zeta: 2\nalpha: 1"),
        ("alpha: 1\nzeta: 2\n", '{"zeta": 2, "alpha": 1}'),
        ("alpha:\n  nothing: null\n", "{alpha: {nothing: ~}}"),
        ("", None),
        ("", "{}"),
        (None, "{}\n"),
        ("{}\n", ""),
    ],
)
def test_extra_vars_are_equal_same_content(old: Any, new: Any) -> None:
    assert extra_vars_are_equal(old, new)


@pytest.mark.parametrize(
    "old, new",
    [
        ("alpha: 1\n", "alpha: 2"),
        ("alpha: 1\n", "alpha: 1\nzeta: 2"),
        ("alpha: 1\n", ""),
        ("alpha: 1\n", "alpha: [1"),
        ("flag: true\n", '{"flag": 1}'),
        ("limit: 1\n", '{"limit": true}'),
        ("ratio: 1\n", "ratio: 1.0"),
        ("items: [1, true]\n", "items: [true, 1]"),
        ("nested:\n  flag: false\n", "nested: {flag: 0}"),
    ],
)
def test_extra_vars_are_equal_different_content(old: Any, new: Any) -> None:
    assert not extra_vars_are_equal(old, new)


def _activation_params(extra_vars: Any) -> dict[str, Any]:
    """Build activation parameters with the given extra_vars."""
    module = MagicMock()
    module.params = {
        "project_name": "project",
        "rulebook_name": "rulebook.yml",
        "decision_environment_name": "de",
        "organization_name": "Default",
        "state": "present",
        "extra_vars": extra_vars,
    }
    with patch(f"{MODULE_PATH}.lookup_resource_id", return_value=1):
        return dict(create_params(module, MagicMock(), is_aap_24=True))


@pytest.mark.parametrize(
    "extra_vars, extra_var",
    [({}, "{}\n"), ("", ""), ({"alpha": 1}, "alpha: 1\n")],
)
def test_create_params_sends_given_extra_vars(extra_vars: Any, extra_var: str) -> None:
    assert _activation_params(extra_vars)["extra_var"] == extra_var


def test_create_params_leaves_omitted_extra_vars_out() -> None:
    assert "extra_var" not in _activation_params(None)


# ---------------------------------------------------------------------------
# main() against a fake EDA API
# ---------------------------------------------------------------------------
ACTIVATION_ID = 10

LOOKUPS = {
    "projects": {"id": 1, "name": "project"},
    "rulebooks": {"id": 2, "name": "rulebook.yml"},
    "decision-environments": {"id": 3, "name": "de"},
    "organizations": {"id": 4, "name": "Default"},
}

DEFINITION: dict[str, Any] = {
    "project_name": "project",
    "rulebook_name": "rulebook.yml",
    "decision_environment_name": "de",
    "organization_name": "Default",
}


class FakeEDA:
    """Stand-in for the EDA API activation endpoints.

    Follows the eda-server rules the module relies on: an activation can only
    be updated while it is disabled and not starting, running or stopping, and
    a PATCH with is_enabled true updates the activation and then starts it.
    Disabling a running activation leaves it stopping until it has been read
    stop_after more times.
    """

    BUSY = ("starting", "running", "stopping", "unresponsive")

    def __init__(
        self, activation: Optional[dict[str, Any]] = None, stop_after: int = 0
    ) -> None:
        self.activation = activation
        self.stop_after = stop_after
        self.requests: list[tuple[str, str]] = []

    @staticmethod
    def running(**fields: Any) -> dict[str, Any]:
        activation = {
            "id": ACTIVATION_ID,
            "name": "activation",
            "description": "",
            "is_enabled": True,
            "status": "running",
            "rulebook_id": 2,
            "decision_environment_id": 3,
            "organization_id": 4,
            "eda_credentials": [],
            "extra_var": "",
            "restart_policy": "on-failure",
            "log_level": "error",
            "enable_persistence": False,
            "restart_on_project_update": False,
        }
        activation.update(fields)
        return activation

    @staticmethod
    def stopped(**fields: Any) -> dict[str, Any]:
        return FakeEDA.running(**{"is_enabled": False, "status": "stopped", **fields})

    def _read(self) -> dict[str, Any]:
        assert self.activation is not None
        if self.activation["status"] == "stopping":
            if self.stop_after > 0:
                self.stop_after -= 1
            else:
                self.activation["status"] = "stopped"
        return dict(self.activation, eda_credentials=[])

    def _start(self) -> None:
        assert self.activation is not None
        self.activation["is_enabled"] = True
        self.activation["status"] = "running"

    def get(self, path: str, **kwargs: Any) -> Mock:
        self.requests.append(("GET", path))
        if path == "config":
            return Mock(status=200, json={})
        if path == f"activations/{ACTIVATION_ID}":
            return Mock(status=200, json=self._read())
        name = kwargs.get("data", {}).get("name")
        if path == "activations":
            item = self._read() if self.activation else None
        else:
            item = LOOKUPS.get(path)
        found = [item] if item and item["name"] == name else []
        return Mock(status=200, json={"count": len(found), "results": found})

    def post(self, path: str, **kwargs: Any) -> Mock:
        self.requests.append(("POST", path))
        if path == "activations":
            data = dict(kwargs["data"])
            is_enabled = data.pop("is_enabled")
            self.activation = self.stopped(id=ACTIVATION_ID, **data)
            if is_enabled:
                self._start()
            return Mock(status=201, json=self._read())
        assert self.activation is not None
        if path.endswith("/disable"):
            if self.activation["is_enabled"]:
                self.activation["is_enabled"] = False
                self.activation["status"] = "stopping"
            return Mock(status=204, json=None)
        if path.endswith("/enable"):
            if not self.activation["is_enabled"]:
                if self.activation["status"] in self.BUSY:
                    raise EDAHTTPError("HTTP error Activation not enabled")
                self._start()
            return Mock(status=204, json=None)
        raise AssertionError(f"Unexpected POST {path}")

    def patch(self, path: str, **kwargs: Any) -> Mock:
        self.requests.append(("PATCH", path))
        assert self.activation is not None
        if self.activation["is_enabled"] or self.activation["status"] in self.BUSY:
            raise EDAHTTPError(
                "HTTP error Activation is not in disabled mode and in stopped status"
            )
        data = dict(kwargs["data"])
        is_enabled = data.pop("is_enabled", False)
        self.activation.update(data)
        if is_enabled:
            self._start()
        return Mock(status=200, json=self._read())


def _run(eda: FakeEDA, check_mode: bool = False, **params: Any) -> MagicMock:
    """Run main() with the given parameters against eda; return the module mock."""
    module = MagicMock()
    module.params = {
        "controller_host": "https://eda.example.com",
        "controller_username": "admin",
        "controller_password": "password",
        "controller_token": None,
        "request_timeout": 10.0,
        "validate_certs": True,
        "name": "activation",
        "new_name": None,
        "description": None,
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
        "state": "present",
        "restart_on_project_update": False,
        "wait": True,
        **params,
    }
    module.check_mode = check_mode
    module.exit_json.side_effect = _AnsibleExit
    module.fail_json.side_effect = _AnsibleExit

    with (
        patch(f"{MODULE_PATH}.AnsibleModule", return_value=module),
        patch(f"{MODULE_PATH}.Client", return_value=eda),
        pytest.raises(_AnsibleExit),
    ):
        main()
    return module


def _exit(module: MagicMock) -> dict[str, Any]:
    module.fail_json.assert_not_called()
    return dict(module.exit_json.call_args.kwargs)


def _failure(module: MagicMock) -> str:
    module.exit_json.assert_not_called()
    return str(module.fail_json.call_args.kwargs["msg"])


@pytest.mark.parametrize("state", ["enabled", "disabled"])
def test_missing_activation_without_definition_fails_clearly(state: str) -> None:
    eda = FakeEDA()

    msg = _failure(_run(eda, state=state, organization_name="Default"))

    assert "activation does not exist" in msg
    assert "project_name, rulebook_name, decision_environment_name" in msg
    assert eda.activation is None


@pytest.mark.parametrize("state, is_enabled", [("enabled", True), ("disabled", False)])
def test_missing_activation_is_created_in_desired_state(
    state: str, is_enabled: bool
) -> None:
    eda = FakeEDA()

    result = _exit(_run(eda, state=state, **DEFINITION))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["is_enabled"] is is_enabled


@pytest.fixture
def no_sleep() -> Any:
    with patch(f"{MODULE_PATH}.time.sleep") as sleep:
        yield sleep


def test_enable_waits_for_stopping_activation(no_sleep: MagicMock) -> None:
    eda = FakeEDA(FakeEDA.stopped(status="stopping"), stop_after=2)

    result = _exit(_run(eda, state="enabled"))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["is_enabled"]
    assert no_sleep.called


def test_update_waits_for_stopping_activation(no_sleep: MagicMock) -> None:
    eda = FakeEDA(FakeEDA.stopped(status="stopping"), stop_after=2)

    result = _exit(_run(eda, description="new", **DEFINITION))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["description"] == "new"
    assert eda.activation["is_enabled"]


def test_no_wait_when_disabled(no_sleep: MagicMock) -> None:
    eda = FakeEDA(FakeEDA.stopped(status="stopping"), stop_after=2)

    msg = _failure(_run(eda, state="enabled", wait=False))

    assert "Activation not enabled" in msg
    no_sleep.assert_not_called()


def test_wait_times_out(no_sleep: MagicMock) -> None:
    eda = FakeEDA(FakeEDA.stopped(status="stopping"), stop_after=100)

    with patch(f"{MODULE_PATH}.WAIT_TIMEOUT", 0):
        msg = _failure(_run(eda, state="enabled"))

    assert "Timeout waiting" in msg
    assert "Last status: stopping" in msg


def test_disabled_with_definition_disables_and_updates_running_activation(
    no_sleep: MagicMock,
) -> None:
    eda = FakeEDA(FakeEDA.running(), stop_after=1)

    result = _exit(_run(eda, state="disabled", description="new", **DEFINITION))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["description"] == "new"
    assert not eda.activation["is_enabled"]


def test_disabled_with_definition_updates_stopped_activation() -> None:
    eda = FakeEDA(FakeEDA.stopped())

    result = _exit(_run(eda, state="disabled", description="new", **DEFINITION))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["description"] == "new"
    assert not eda.activation["is_enabled"]


def test_disabled_with_unchanged_definition_is_idempotent() -> None:
    eda = FakeEDA(FakeEDA.stopped())

    result = _exit(_run(eda, state="disabled", **DEFINITION))

    assert not result["changed"]
    assert ("PATCH", "activations") not in eda.requests


def test_disabled_without_definition_only_disables() -> None:
    eda = FakeEDA(FakeEDA.running())

    result = _exit(_run(eda, state="disabled", description="new"))

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["description"] == ""
    assert not eda.activation["is_enabled"]


def test_partial_definition_warns() -> None:
    eda = FakeEDA(FakeEDA.stopped())

    module = _run(eda, state="disabled", project_name="project")

    module.warn.assert_called_once()
    assert "decision_environment_name" in module.warn.call_args.args[0]


def test_disabled_with_definition_in_check_mode_changes_nothing() -> None:
    eda = FakeEDA(FakeEDA.running())

    result = _exit(
        _run(eda, check_mode=True, state="disabled", description="new", **DEFINITION)
    )

    assert result["changed"]
    assert eda.activation is not None
    assert eda.activation["is_enabled"]
    assert [method for method, _ in eda.requests] == ["GET"] * len(eda.requests)


def test_disabled_with_definition_without_wait_fails_while_stopping() -> None:
    eda = FakeEDA(FakeEDA.running(), stop_after=1)

    msg = _failure(
        _run(eda, state="disabled", description="new", wait=False, **DEFINITION)
    )

    assert "not in disabled mode and in stopped status" in msg
