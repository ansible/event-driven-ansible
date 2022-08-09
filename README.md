# Collection for Event Driven Automation

This collection contains examples of how to use event driven automation
using [ansible-events](https://github.com/benthomasson/ansible-events).

This collection contains the following example rulesets:

* [hello_events.yml](benthomasson/eda/rules/hello_events.yml)

And the following example event sources:

* [alertmanager](benthomasson/eda/plugins/event_source/alertmanager.py)
* [azure_service_bus](benthomasson/eda/plugins/event_source/azure_service_bus.py)
* [file](benthomasson/eda/plugins/event_source/file.py)
* [kafka](benthomasson/eda/plugins/event_source/kafka.py)
* [range](benthomasson/eda/plugins/event_source/range.py)
* [url_check](benthomasson/eda/plugins/event_source/url_check.py)
* [webhook](benthomasson/eda/plugins/event_source/webhook.py)
* [watchdog](benthomasson/eda/plugins/event_source/watchdog.py)


You can run these examples using an execution environment
that is available on quay.io.  Get the EE using the following command:

    docker pull quay.io/bthomass/ansible-events

Then run the hello events example using:

    docker run -it quay.io/bthomass/ansible-events:latest ansible-events --rules benthomasson.eda.hello_events -i inventory.yml


You can build your own execution environment for running event
driven automation using this repo as a starting point: http://github.com/benthomasson/ansible-events-ee
