# Collection for Event Driven Ansible

This collection contains source plugins, playbooks and examples to use with [ansible-rulebook](https://github.com/ansible/ansible-rulebook).

## Install

You can install the Ansible Events collection with the Ansible Galaxy CLI:

```
ansible-galaxy collection install ansible.eda
```

The python module dependencies are not installed by ansible-galaxy. They can be manually installed using pip:

```
pip install requirements.txt
```

or

```
pip install aiohttp aiokafka watchdog azure-servicebus asyncio
```

## Content

### Rulesets

This collection contains the following example rulesets:

* [hello_events.yml](rulebooks/hello_events.yml)

### Source plugins

And the following example event sources:

* [alertmanager](plugins/event_source/alertmanager.py)
* [azure_service_bus](plugins/event_source/azure_service_bus.py)
* [file](plugins/event_source/file.py)
* [kafka](plugins/event_source/kafka.py)
* [range](plugins/event_source/range.py)
* [url_check](plugins/event_source/url_check.py)
* [webhook](plugins/event_source/webhook.py)
* [watchdog](plugins/event_source/watchdog.py)

### Playbooks

**Install ansible-rulebook CLI**

This collection provides a playbook to install ansible-rulebook.
Only Fedora and Mac os are supported for now.

First, you must create an inventory. For example:

```yaml
all:
  hosts:
    localhost:
      ansible_connection: local
```

Then, you can run the playbook:

```sh
ansible-playbook -i myinventory.yml ansible.eda.install-rulebook-cli
```

### Examples

You can run these examples using an execution environment
that is available on quay.io. Get the EE using the following command:

    docker pull quay.io/bthomass/ansible-rulebook

Then run the hello events example using:

    docker run -it quay.io/bthomass/ansible-rulebook:latest ansible-rulebook --rules ansible.eda.hello_events -i inventory.yml

You can build your own execution environment for running event
driven automation using this repo as a starting point: <http://github.com/benthomasson/ansible-rulebook-ee>

# Running tests for source plugins

Test requirements must be installed:

```sh
pip install -r test_requirements.txt
```

## Integration tests

Currently integration tests require [docker](https://docs.docker.com/engine/install/)/[podman](https://podman.io/getting-started/installation) and [docker-compose](https://docs.docker.com/compose/install/)

```

ansible-galaxy collection install .
pytest tests/integration
```

## Sanity tests

```sh
ansible-test sanity
```

## Units tests

```sh
ansible-test units
```