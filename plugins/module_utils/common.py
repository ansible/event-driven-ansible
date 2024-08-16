# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

from typing import Any, Optional, Union

__metaclass__ = type


def to_list_of_dict(
    result: Optional[Union[dict[str, bool], list[dict[Any, Any]]]]
) -> list[dict]:
    if result is None:
        return []
    if not isinstance(result, list):
        return [result]
    return result
