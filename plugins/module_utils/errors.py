# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Custom exceptions for Event-Driven Ansible.

This module defines the exception hierarchy for error handling
when working with the Event-Driven Ansible controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class EDAError(Exception):
    """Base exception for Event-Driven Ansible errors.

    This is the parent class for all EDA-specific exceptions,
    used for general error handling in the module.
    """


class EDAHTTPError(EDAError):
    """Exception for HTTP errors when interacting with EDA API.

    Raised when there are problems with HTTP requests to the EDA controller,
    such as network errors, invalid responses, or parsing issues.
    """


class AuthError(EDAError):
    """Exception for authentication errors.

    Raised when authentication with the EDA controller fails,
    for example, due to invalid credentials or an expired token.
    """
