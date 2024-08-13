# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


class EDAError(Exception):
    pass


class EDAHTTPError(EDAError):
    pass


class AuthError(EDAError):
    pass
