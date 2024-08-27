# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Literal, Optional, Union
from unittest.mock import MagicMock, Mock

import pytest
from ansible_collections.ansible.eda.plugins.module_utils.controller import (  # type: ignore
    Controller,
)
from ansible_collections.ansible.eda.plugins.module_utils.errors import (  # type: ignore
    EDAError,
)

ENDPOINT = "test_endpoint"


@pytest.fixture
def mock_client() -> Mock:
    return Mock()


@pytest.fixture
def mock_module() -> Mock:
    module = Mock()
    module.params = {"update_secrets": True}
    module.check_mode = False
    return module


@pytest.fixture
def controller(mock_client: Mock, mock_module: Mock) -> Controller:
    return Controller(client=mock_client, module=mock_module)


@pytest.mark.parametrize(
    "new_item, mock_response, expected_result, expected_calls",
    [
        (
            {"name": "Test"},
            Mock(status=201, json={"id": 1}),
            {"changed": True, "id": 1},
            1,  # Expected number of post calls
        ),
    ],
)
def test_create_if_needed(
    mock_client: Mock,
    controller: Controller,
    new_item: dict[str, str],
    mock_response: Mock,
    expected_result: dict[str, Union[bool, int]],
    expected_calls: Literal[1],
) -> None:
    if mock_response:
        mock_client.post.return_value = mock_response
    result = controller.create_if_needed(new_item, ENDPOINT)
    assert result == expected_result
    assert mock_client.post.call_count == expected_calls
    if expected_calls > 0:
        mock_client.post.assert_called_with(ENDPOINT, **{"data": new_item})


@pytest.mark.parametrize(
    "existing_item, mock_response, expected_result, expected_calls",
    [
        # delete_if_needed with an existing item
        (
            {"id": 1, "name": "test_item"},
            Mock(status=204, json={}),
            {"changed": True, "id": 1},
            1,  # Expected number of delete calls
        ),
        # delete_if_needed without an existing item
        (
            None,
            None,
            {"changed": False},
            0,  # Expected number of delete calls
        ),
    ],
)
def test_delete_if_needed(
    mock_client: Mock,
    controller: Controller,
    existing_item: dict[str, Union[int, str]],
    mock_response: Optional[Mock],
    expected_result: dict[str, Union[bool, int]],
    expected_calls: Union[Literal[1], Literal[0]],
) -> None:
    if mock_response:
        mock_client.delete.return_value = mock_response

    result = controller.delete_if_needed(existing_item, ENDPOINT)
    assert result == expected_result
    assert mock_client.delete.call_count == expected_calls
    if expected_calls > 0:
        mock_client.delete.assert_called_with(ENDPOINT, **{"id": existing_item["id"]})


def test_update_if_needed_with_existing_item(
    mock_client: Mock, controller: Controller
) -> None:
    existing_item = {"id": 1, "name": "Test1"}
    new_item = {"name": "Test2"}
    response = Mock(status=200, json={"id": 1, "name": "Test2"})
    mock_client.patch.return_value = response
    result = controller.update_if_needed(
        existing_item, new_item, ENDPOINT, "resource type"
    )
    mock_client.patch.assert_called_with(ENDPOINT, **{"data": new_item, "id": 1})
    assert result["changed"] is True
    assert result["id"] == 1


def test_get_endpoint(mock_client: Mock, controller: Controller) -> None:
    response = Mock(status=200, json={"count": 1, "results": [{"id": 1}]})
    mock_client.get.return_value = response
    result = controller.get_endpoint(ENDPOINT)
    mock_client.get.assert_called_with(ENDPOINT)
    assert result == response


def test_post_endpoint(mock_client: Mock, controller: Controller) -> None:
    response = Mock(status=201, json={"id": 1})
    mock_client.post.return_value = response
    result = controller.post_endpoint(ENDPOINT)
    mock_client.post.assert_called_with(ENDPOINT)
    assert result == response


def test_patch_endpoint_check_mode(controller: Controller) -> None:
    controller.module.check_mode = True
    result = controller.patch_endpoint(ENDPOINT)
    assert result["changed"] is True


def test_get_name_field_from_endpoint() -> None:
    assert Controller.get_name_field_from_endpoint("users") == "username"
    assert Controller.get_name_field_from_endpoint("unknown") == "name"


@pytest.mark.parametrize(
    "item, expected_name, should_raise",
    [
        ({"name": "test_item"}, "test_item", False),
        ({"username": "test_user"}, "test_user", False),
        ({}, None, True),
    ],
)
def test_get_item_name(
    controller: Controller,
    item: dict[str, str],
    expected_name: Optional[Union[Literal["test_item"], Literal["test_user"]]],
    should_raise: bool,
) -> None:
    if should_raise:
        with pytest.raises(EDAError):
            controller.get_item_name(item)
    else:
        assert controller.get_item_name(item) == expected_name


def test_has_encrypted_values() -> None:
    assert Controller.has_encrypted_values({"key": "$encrypted$"}) is True
    assert Controller.has_encrypted_values({"key": "value"}) is False


def test_fail_wanted_one(mock_client: Mock, controller: Controller) -> None:
    response = MagicMock()
    response.json.return_value = {"count": 2, "results": [{"id": 1}, {"id": 2}]}
    mock_client.build_url.return_value.geturl.return_value = "http://example.com/api"
    mock_client.host = "http://example.com"
    with pytest.raises(EDAError, match="expected 1"):
        controller.fail_wanted_one(response)


def test_fields_could_be_same() -> None:
    assert (
        Controller.fields_could_be_same({"key": "$encrypted$"}, {"key": "value"})
        is True
    )
    assert (
        Controller.fields_could_be_same({"key1": "value1"}, {"key2": "value2"}) is False
    )


@pytest.mark.parametrize(
    "old, new, expected",
    [
        ({"key": "$encrypted$"}, {"key": "value"}, True),
        ({"key": "value"}, {"key": "value"}, False),
    ],
)
def test_objects_could_be_different(
    controller: "Controller", old: dict[str, str], new: dict[str, str], expected: bool
) -> None:
    assert controller.objects_could_be_different(old, new) is expected
