DOCUMENTATION = """
---
module: credential_type_info
author:
    - Alina Buzachis (@alinabuzachis)
short_description: List credential types in EDA Controller
description:
    - List credentail types in EDA controller.
version_added: 2.0.0
options:
    name:
      description:
        - The name of the credential type.
      type: str
      required: false
requirements:
  - The 'requests' Python module must be installed.
extends_documentation_fragment:
    - ansible.eda.eda_controller.auths
"""


EXAMPLES = """
    - name: Get information about a credential type
      ansible.eda.credential_type_info:
        name: "Test"

    - name: List all credential types
      ansible.eda.credential_type:
"""


RETURN = """ # """


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.eda.plugins.module_utils.client import Client
from ansible_collections.ansible.eda.plugins.module_utils.controller import Controller

from ..module_utils.arguments import AUTH_ARGSPEC


def main():
    argument_spec = dict(
        name=dict(type="str", required=False),
    )

    argument_spec.update(AUTH_ARGSPEC)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    client = Client(
        host=module.params.get("controller_host"),
        username=module.params.get("controller_username"),
        password=module.params.get("controller_password"),
        timeout=module.params.get("request_timeout"),
        validate_certs=module.params.get("validate_certs"),
    )

    name = module.params.get("name")
    controller = Controller(client, module)

    # Attempt to look up credential_type based on the provided name
    result = controller.get_one_or_many("credential-types", name=name, want_one=False)

    module.exit_json(result=result)


if __name__ == "__main__":
    main()
