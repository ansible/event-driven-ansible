import pytest

from plugins.event_filter.insert_source_info import main as sources_main

EVENT_DATA_1 = [
    (
        {"myevent": {"name": "fred"}},
        {"source_name": "my_source", "source_type": "stype"},
        {
            "myevent": {"name": "fred"},
            "meta": {"source": {"name": "my_source", "type": "stype"}},
        },
    ),
    (
        {
            "myevent": {"name": "barney"},
            "meta": {"source": {"name": "origin", "type": "regular"}},
        },
        {"source_name": "my_source", "source_type": "stype"},
        {
            "myevent": {"name": "barney"},
            "meta": {"source": {"name": "origin", "type": "regular"}},
        },
    ),
]


@pytest.mark.parametrize("data, args, expected", EVENT_DATA_1)
def test_sources_main(data, args, expected):
    data = sources_main(data, **args)
    assert data == expected
