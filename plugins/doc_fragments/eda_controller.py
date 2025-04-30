# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    AUTHS = """
options:
    controller_host:
        description:
          - The URL of the EDA controller.
          - If not set, the value of C(CONTROLLER_HOST), or E(AAP_HOSTNAME) environment variables will be used.
          - Support for E(AAP_HOSTNAME) has been added in version 2.7.
        required: true
        type: str
        version_added: '2.0.0'
        aliases: [ aap_hostname ]
    controller_username:
        description:
          - Username used for authentication.
          - If not set, the value of C(CONTROLLER_USERNAME), or E(AAP_USERNAME) environment variables will be used.
          - Support for E(AAP_USERNAME) has been added in version 2.7.
        type: str
        version_added: '2.0.0'
        aliases: [ aap_username ]
    controller_password:
        description:
          - Password used for authentication.
          - If not set, the value of C(CONTROLLER_PASSWORD), or E(AAP_PASSWORD) environment variables will be used.
          - Support for E(AAP_PASSWORD) has been added in version 2.7.
        type: str
        version_added: '2.0.0'
        aliases: [ aap_password ]
    request_timeout:
        description:
          - Timeout in seconds for the connection with the EDA controller.
          - If not set, the value of C(CONTROLLER_TIMEOUT), E(AAP_REQUEST_TIMEOUT) environment variables
          - will be used.
          - Support for E(AAP_REQUEST_TIMEOUT) has been added in version 2.7.
        type: float
        default: 10
        version_added: '2.0.0'
        aliases: [ aap_request_timeout ]
    validate_certs:
        description:
          - Whether to allow insecure connections to Ansible Automation Platform EDA
            Controller instance.
          - If C(no), SSL certificates will not be validated.
          - This should only be used on personally controlled sites using self-signed certificates.
          - If value not set, will try environment variable C(CONTROLLER_VERIFY_SSL), or E(AAP_VALIDATE_CERTS).
          - Support for E(AAP_VALIDATE_CERTS) has been added in version 2.7.
        default: True
        type: bool
        version_added: '2.0.0'
        aliases: [ aap_validate_certs ]
"""
