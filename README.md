# Collection for Event Driven Ansible

This collection contains examples of how to use event driven automation
using [ansible-rulebook](https://github.com/ansible/ansible-rulebook).

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

This collection contains the following example rulesets:

* [hello_events.yml](rules/hello_events.yml)

And the following example event sources:

* [alertmanager](plugins/event_source/alertmanager.py)
* [azure_service_bus](plugins/event_source/azure_service_bus.py)
* [file](plugins/event_source/file.py)
* [kafka](plugins/event_source/kafka.py)
* [range](plugins/event_source/range.py)
* [url_check](plugins/event_source/url_check.py)
* [webhook](plugins/event_source/webhook.py)
* [watchdog](plugins/event_source/watchdog.py)

You can run these examples using an execution environment
that is available on quay.io.  Get the EE using the following command:

    docker pull quay.io/bthomass/ansible-events

Then run the hello events example using:

    docker run -it quay.io/bthomass/ansible-events:latest ansible-events --rules ansible.eda.hello_events -i inventory.yml

You can build your own execution environment for running event
driven automation using this repo as a starting point: <http://github.com/benthomasson/ansible-events-ee>

# Integration tests

Currently integration tests require [docker](https://docs.docker.com/engine/install/)/[podman](https://podman.io/getting-started/installation) and [docker-compose](https://docs.docker.com/compose/install/)

**NOTE: dependency on private repositories**

You must [create a personal github token](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in order to be able to work with private repos and export it:

```
export GITHUB_TOKEN=your token
```


```
pip install -r test_requirements.txt
ansible-galaxy collection install .
pytest tests/integration
```
