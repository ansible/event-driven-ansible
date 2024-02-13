# Collection for Event-Driven Ansible

This collection contains event source plugins, event filters and example rulebooks to be used with [eda-server](https://github.com/ansible/eda-server).
Eda-collection is intended to provide the initial resources for getting started with the [eda-server](https://github.com/ansible/eda-server) Other third-party integrations should be delegated to the collections developed by the ansible community.
Some of the existing plugins in this collection that do not fit as well in the scope of the collection are just keep them there for backward compatibility. 
They will be eventually deprecated at some point.

<p style="text-align: center" align="center">
    <a href="https://github.com/ansible/event-driven-ansible/actions?workflow=integration-tests"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/integration-tests.yml/badge.svg?event=schedule"/> </a>
    <a href="https://github.com/ansible/event-driven-ansible/actions?workflow=linters"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/linters.yml/badge.svg?event=schedule"/> </a>
    <a href="https://github.com/ansible/event-driven-ansible/actions?workflow=tests"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/tests.yml/badge.svg?event=schedule"/> </a>
    <a href="https://github.com/ansible/event-driven-ansible/actions?workflow=tox"><img height="20px" src="https://github.com/ansible/event-driven-ansible/actions/workflows/tox.yml/badge.svg?event=schedule"/> </a>
</p>

## Requirements

* ansible-rulebook >= 1.0.0
* python >= 3.9
* ansible >= 2.13

## Install

Install the ansible.eda collection with the Ansible Galaxy CLI:

```
ansible-galaxy collection install ansible.eda
```

The python module dependencies are not installed by ansible-galaxy. They must be installed manually using pip:

```
pip install -r requirements.txt
```

## Contributing

Please refer to the [contributing guide](./CONTRIBUTING.md) for information about how you can contribute to the project.
