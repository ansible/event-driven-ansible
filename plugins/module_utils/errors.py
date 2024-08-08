# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations


class EDAHTTPError(Exception):
    pass


class AuthError(EDAHTTPError):
    pass
