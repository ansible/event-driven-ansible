# Collection for Event-Driven Ansible

This collection contains event source plugins, event filters and example rulebooks to be used with [ansible-rulebook](https://ansible-rulebook.readthedocs.io/en/stable/) or [eda-server](https://github.com/ansible/eda-server).
Eda-collection is intended to provide the initial resources for getting started with the [eda-server](https://github.com/ansible/eda-server). Other third-party integrations should be delegated to the collections developed by the ansible community.
Some of the existing plugins in this collection that do not fit as well in the scope of the collection are just keep them there for backward compatibility. 
They will be eventually deprecated at some point.

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
