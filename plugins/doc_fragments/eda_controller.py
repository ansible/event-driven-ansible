# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:

    AUTHS = """
options:
    controller_host:
        description:
          - The URL of the EDA controller.
          - If not set, the value of the C(CONTROLLER_URL) environment variable will be used.
        required: true
        type: str
        version_added: '2.0.0'
    controller_username:
        description:
          - Username used for authentication.
          - If not set, the value of the C(CONTROLLER_USERNAME) environment variable will be used.
        type: str
        version_added: '2.0.0'
    controller_password:
        description:
          - Password used for authentication.
          - If not set, the value of the C(CONTROLLER_PASSWORD) environment variable will be used.
        type: str
        version_added: '2.0.0'
    request_timeout:
        description:
          - Timeout in seconds for the connection with the EDA controller.
          - If not set, the value of the C(CONTROLLER_TIMEOUT) environment variable will be used.
        type: float
        default: 10
        version_added: '2.0.0'
    validate_certs:
        description:
          - Whether to allow insecure connections to Ansible Automation Platform EDA
            Controller instance.
          - If C(no), SSL certificates will not be validated.
          - This should only be used on personally controlled sites using self-signed certificates.
          - If value not set, will try environment variable C(CONTROLLER_VERIFY_SSL)
        default: True
        type: bool
        version_added: '2.0.0'
"""
