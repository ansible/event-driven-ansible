#!/usr/bin/python

# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: upcase
short_description: Upper cases a passed in string

version_added: "1.0.0"

description: Upper cases a passed in string, if the passed in string is already uppercased changed is set to false.
    To have the module generate an error send the string fail

options:
    name:
        description: This is the string sent to the upcase module.
        required: true
        type: str
author:
    - Test User (@yourGitHubHandle)
"""  # noqa: E501

EXAMPLES = r"""
# Pass in a message
- name: Test with a lower string
  ansible.eda.upcase:
    name: hello world

# pass in a message and have it fail
- name: Test with a fail message
  ansible.eda.upcase:
    name: fail
"""

RETURN = r"""
message:
    description: The result message that the upcase module generates.
    type: str
    returned: always
    sample: 'HELLO WORLD'
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def run_module():
    module_args = dict(name=dict(type="str", required=True))

    result = dict(changed=False, message="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params["name"] == "fail":
        module.fail_json(msg="You requested this to fail", **result)

    # Success
    result["message"] = module.params["name"].upper()
    result["changed"] = result["message"] != module.params["name"]
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
