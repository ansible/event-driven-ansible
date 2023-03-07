import pytest

from plugins.event_filter.insert_hosts_to_meta import main as hosts_main

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
def test_find_hosts(data, args, expected_hosts):
    data = hosts_main(data, **args)
    if expected_hosts:
        assert data["meta"]["hosts"] == expected_hosts
    else:
        assert "hosts" not in data["meta"]


EVENT_DATA_2 = [
    (
        {"app": {"target": 5000}},
        {"host_path": "app.target"},
    ),
    (
        {"app": {"target": ("host1", 5000)}},
        {"host_path": "app.target"},
    ),
    (
        {"app": {"target": {"foo": "bar"}}},
        {"host_path": "app.target"},
    ),
]


@pytest.mark.parametrize("data, args", EVENT_DATA_2)
def test_fail_find_hosts(data, args):
    with pytest.raises(TypeError):
        hosts_main(data, **args)
