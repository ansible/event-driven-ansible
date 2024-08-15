# Collection for Event-Driven Ansible

This collection contains event source plugins, event filters and example rulebooks to be used with [ansible-rulebook](https://ansible-rulebook.readthedocs.io/en/stable/).

<a href="https://github.com/ansible/event-driven-ansible/actions?workflow=tox"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/tox.yml/badge.svg?event=schedule"/> </a>

## Description

The primary purpose of this collection is to to reduce manual tasks and deliver more efficient mission-critical workflows. By leveraging this collection, organizations can automate a variety of error-prone and time-consuming tasks and respond to changing conditions in any IT domain across IT environments for better agility and resiliency.

## Requirements

### Ansible version compatibility

Tested with the Ansible Core >= 2.15.0 versions, and the current development version of Ansible. Ansible Core versions prior to 2.15.0 are not supported.

### Python version compatibility

This collection requires Python 3.9 or greater.

### Additional dependencies

This collection requires ansible-rulebook 1.0.0 or greater.

## Installation

The ansible.eda collection can be installed with Ansible Galaxy command-line tool:

```shell
ansible-galaxy collection install ansible.eda
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: ansible.eda
```

Note that if you install any collections from Ansible Galaxy, they will not be upgraded automatically when you upgrade the Ansible package.
To upgrade the collection to the latest available version, run the following command:

```
ansible-galaxy collection install ansible.eda --upgrade
```

A specific version of the collection can be installed by using the `version` keyword in the `requirements.yml` file:

```yaml
---
collections:
  - name: ansible.eda
    version: 1.0.0
```

or using the ansible-galaxy command as follows

```
ansible-galaxy collection install ansible.eda:==1.0.0
```

The python module dependencies are not installed by ansible-galaxy. They must be installed manually using pip:

```shell
pip install -r requirements.txt
```

Refer the following for more details.
* [using Ansible collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Use Cases

You can either call modules, rulebooks and playbook by their Fully Qualified Collection Name (FQCN), such as ansible.eda.activation, or you can call modules by their short name if you list the ansible.eda collection in the playbook's collections keyword:

```
---
  - name: Create a rulebook activation
    ansible.eda.activation:
      name: "Example Activation"
      description: "Example Activation description"
      project: "Example Project"
      rulebook_name: "basic_short.yml"
      decision_environment_name: "Example Decision Environment"
      enabled: False
      awx_token_id: 1

  - name: Get information about the rulebook activation
    ansible.eda.activation_info:
      name: "Example Activation"

  - name: Delete rulebook activation
    ansible.eda.activation:
      name: "Example Activation"
      state: absent
```

## Contributing

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Event-Driven Ansible collection repository](https://github.com/ansible/event-driven-ansible).
See [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.

### More information about contributing

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly

## Release notes

See the [raw generated changelog](https://github.com/ansible/event-driven-ansible/tree/main/CHANGELOG.rst).

## Related Information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collection Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## License Information

See [LICENSE](./LICENSE) to see the full text.
