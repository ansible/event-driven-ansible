# Collection for Event-Driven Ansible

This collection contains event source plugins, event filters and example rulebooks to be used with [ansible-rulebook](https://ansible-rulebook.readthedocs.io/en/stable/).

<a href="https://github.com/ansible/event-driven-ansible/actions?workflow=tox"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/tox.yml/badge.svg?event=schedule"/> </a>

## Requirements

* python >= 3.9
* ansible-core >= 2.15

## Install

Install the ansible.eda collection with the Ansible Galaxy CLI:

```shell
ansible-galaxy collection install ansible.eda
```

The Python module dependencies are not installed by ansible-galaxy. They must be installed manually using pip:

```shell
pip install -r requirements.txt
```

## Contributing

Please refer to the [contributing guide](./CONTRIBUTING.md) for information about how you can contribute to the project.
