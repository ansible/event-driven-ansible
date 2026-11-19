# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


@pytest.fixture
def build_module():
    """Instantiate an AnsibleModule with the given argument spec and args.

    ansible-core reads module arguments from ``basic._ANSIBLE_ARGS``. The
    original value is restored after the test so tests do not leak state.
    """

    original = getattr(basic, "_ANSIBLE_ARGS", None)
    original_profile = getattr(basic, "_ANSIBLE_PROFILE", None)

    def _build(argument_spec, params):
        basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": params}))
        # ansible-core >= 2.19 requires a serialization profile; older
        # versions ignore the attribute.
        basic._ANSIBLE_PROFILE = "legacy"
        return basic.AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
        )

    yield _build
    basic._ANSIBLE_ARGS = original
    basic._ANSIBLE_PROFILE = original_profile
