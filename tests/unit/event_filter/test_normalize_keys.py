import pytest

from extensions.eda.plugins.event_filter.normalize_keys import main as normalize_main

TEST_DATA_1 = [
    (
        {"app": {"tar/get": "web/server"}},
        True,
        {"app": {"tar_get": "web/server"}},
    ),
    (
        {"a.p.p": {"t?r/get": "?web/server"}},
        True,
        {"a_p_p": {"t_r_get": "?web/server"}},
    ),
    (
        {"key1": {"key2": {"key?/+12-*": "?web/server"}}},
        True,
        {"key1": {"key2": {"key_12_": "?web/server"}}},
    ),
    (
        {"key1": {"key?2": "abc", "key_2": "345"}},
        False,
        {"key1": {"key_2": "345"}},
    ),
    (
        {"key1": {"key_2": "abc", "key?2": "345"}},
        True,
        {"key1": {"key_2": "345"}},
    ),
    (
        {"key1": [{"key/2": "abc"}, {"key?2": "345"}]},
        True,
        {"key1": [{"key_2": "abc"}, {"key_2": "345"}]},
    ),
    (
        {"key1": [{"key/2": "abc"}, 5]},
        True,
        {"key1": [{"key_2": "abc"}, 5]},
    ),
]


@pytest.mark.parametrize("event, overwrite, updated_event", TEST_DATA_1)
def test_normalize_keys(event: dict, overwrite: bool, updated_event: dict) -> None:
    data = normalize_main(event, overwrite)
    assert data == updated_event
