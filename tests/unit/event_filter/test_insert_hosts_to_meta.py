from typing import Any

import pytest

from extensions.eda.plugins.event_filter.insert_hosts_to_meta import PathNotExistError
from extensions.eda.plugins.event_filter.insert_hosts_to_meta import main as hosts_main

EVENT_DATA_1 = [
    (
        {"app": {"target": "webserver"}},
        {"host_path": "app.target"},
        ["webserver"],
    ),
    (
        {"app": {"target": "webserver;postgres"}},
        {
            "host_path": "app/target",
            "path_separator": "/",
            "host_separator": ";",
        },
        ["webserver", "postgres"],
    ),
    (
        {
            "app": {"target": ["webserver", "postgres"]},
            "meta": {"source": "upstream"},
        },
        {
            "host_path": "app.target",
        },
        ["webserver", "postgres"],
    ),
    (
        {"app": "foo", "meta": {"source": "upstream"}},
        {
            "host_path": "bar",
        },
        [],
    ),
]


@pytest.mark.parametrize("data, args, expected_hosts", EVENT_DATA_1)
def test_find_hosts(
    data: dict[str, Any], args: dict[str, str], expected_hosts: list[str]
) -> None:
    data = hosts_main(data, **args)  # type: ignore
    if expected_hosts:
        assert data["meta"]["hosts"] == expected_hosts
    else:
        assert "hosts" not in data["meta"]


@pytest.mark.parametrize(
    "data, args",
    [
        pytest.param(
            {"app": {"target": 5000}},
            {"host_path": "app.target"},
        ),
        pytest.param(
            {"app": {"target": ("host1", 5000)}},
            {"host_path": "app.target"},
        ),
        pytest.param(
            {"app": {"target": {"foo": "bar"}}},
            {"host_path": "app.target"},
        ),
    ],
)
def test_fail_find_hosts(data: dict[str, Any], args: dict[str, str]) -> None:
    with pytest.raises(TypeError):
        hosts_main(data, **args)  # type: ignore


def test_host_path_not_exist() -> None:
    event = {"app": {"target": 5000}}
    host_path = "app.bad"
    assert hosts_main(event, host_path=host_path) == event


def test_host_path_not_exist_exception() -> None:
    event = {"app": {"target": 5000}}
    host_path = "app.bad"
    with pytest.raises(PathNotExistError):
        hosts_main(event, host_path=host_path, raise_error=True)
