# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Nikhil Jain <nikjain@redhat.com> GNU General Public
# License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Automation Platform EDA Controller documentation fragment
    DOCUMENTATION = r"""
options:
  eda_controller_host:
    description:
    - URL to your Ansible Automation Platform EDA Controller instance.
    - If value not set, will try environment variable C(EDA_CONTROLLER_HOST)
    type: str
  eda_controller_username:
    description:
    - Username for your Ansible Automation Platform EDA Controller instance.
    - If value not set, will try environment variable C(EDA_CONTROLLER_USERNAME)
    type: str
  eda_controller_password:
    description:
    - Password for your Ansible Automation Platform EDA Controller instance.
    - If value not set, will try environment variable C(EDA_CONTROLLER_PASSWORD)
    type: str
  validate_certs:
    description:
    - Whether to allow insecure connections to Ansible Automation Platform EDA
      Controller instance.
    - If C(no), SSL certificates will not be validated.
    - This should only be used on personally controlled sites using self-signed
      certificates.
    - If value not set, will try environment variable C(EDA_CONTROLLER_VERIFY_SSL)
    type: bool
  request_timeout:
    description:
    - Specify the timeout Ansible should use in requests to the eda controller host.
    - Defaults to 10s, but this is handled by the shared module_utils code
    - If value not set, will try environment variable C(EDA_CONTROLLER_REQUEST_TIMEOUT)
    type: float
"""
