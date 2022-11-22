# Event-Driven Ansible

## What is it?

Event-Driven Ansible is a new way to enhance and expand automation. It improves IT speed and agility, while enabling consistency and resilience. The Event-Driven Ansible technology was developed by Red Hat and is available as a developer preview. Community input is essential. Since we are building a solution to best meet your needs, we're providing an opportunity for you to advocate for those needs.

Event-Driven Ansible is designed for simplicity and flexibility. By writing an Ansible Rulebook (similar to Ansible Playbooks, but more oriented to "if-then" scenarios) and allowing Event-Driven Ansible to subscribe to an event listening source, your teams can more quickly and easily automate a variety of tasks across the organization. EDA is providing a way of codifying operational logic.

## Why Event-Driven?

Automation allows us to give our systems and technology speed and agility while minimizing human error. However, when it comes to trouble tickets and issues, we are often left to traditional and often manual methods of troubleshooting and information gathering. We inherently slow things down and interrupt our businesses. We have to gather information, try our common troubleshooting steps, confirm with different teams.

One application of Event-Driven Ansible is to codify this operation knowledge in order to remediate technology issues near real-time, or at least trigger troubleshooting and information collection in an attempt to find the root cause of an outage while your support teams handle other issues.

Event-Driven Ansible has the potential to change the way we respond to issues and illuminates many new automation possibilities.

It opens up the possibilities of faster resolution and greater automated observation of our environments.

## Getting Started

Now, let's install ansible-rulebook and start with our very first event.

To install ansible-rulebook, we can install our Galaxy Collection, which has a playbook to install everything we need.

`ansible-galaxy collection install ansible.eda`

Once the Collection is installed, you can run the install_rulebook_cli.yml playbook. The following example would install ansible-rulebook CLI on your local system:

`ansible-playbook -i localhost, -c local ansible.eda.install_rulebook_cli`

**Note:** Some tasks in this role require [privilege escalation](https://docs.ansible.com/ansible/latest/plugins/become.html) and therefore you may need to provide the necessary credentials.

This will install everything you need to get started with ansible-rulebook on the command line. Currently support systems can be found in the role's [meta file](roles/install_ansible_rulebook/meta/main.yml).

If you want to contribute to ansible-rulebook, you can also fork the following [GitHub repository](https://github.com/ansible/ansible-rulebook). This repository also contains instructions for setting up your development environment and how to build a test container.

Let's build an example rulebook that will trigger an action from a webhook. We will be looking for a specific payload from the webhook, and if that condition is met from the webhook event, then ansible-rulebook with trigger the desired action. Below is our example rulebook:

```
---
- name: Listen for events on a webhook
  hosts: all

  ## Define our source for events

  sources:
    - ansible.eda.webhook:
        host: 0.0.0.0
        port: 5000

  ## Define the conditions we are looking for

  rules:
    - name: Say Hello
      condition: event.payload.message == "Ansible is super cool"

  ## Define the action we should take should the condition be met

      action:
        run_playbook:
          name: say-what.yml
```

The playbook `say-what.yml`:

```
- hosts: localhost
  connection: local
  tasks:
    - debug:
        msg: "Thank you, my friend!"
```

If we look at this example, we can see the structure of the rulebook. Our sources, rules and actions are defined. We are using the webhook source plugin from our ansible.eda collection, and we are looking for a message payload from our webhook that contains "Ansible is super cool". Once this condition has been met, our defined action will trigger which in this case is to trigger a playbook.

One important thing to take note of ansible-rulebook is that it is not like ansible-playbook which runs a playbook and once the playbook has been completed it will exit. With ansible-rulebook, it will continue to run waiting for events and matching those events, it will only exit upon a shutdown action or if there is an issue with the event source itself, for example if a website you are watching with the url-check plugin stops working.

With our rulebook built, we will simply tell ansible-rulebook to use it as a ruleset and wait for events:

```
root@ansible-rulebook:/root# ansible-rulebook --rulebook webhook-example.yml -i inventory.yml --verbose

INFO:ansible_events:Starting sources
INFO:ansible_events:Starting sources
INFO:ansible_events:Starting rules
INFO:root:run_ruleset
INFO:root:{'all': [{'m': {'payload.message': 'Ansible is super cool!'}}], 'run': <function make_fn.<locals>.fn at 0x7ff962418040>}
INFO:root:Waiting for event
INFO:root:load source
INFO:root:load source filters
INFO:root:Calling main in ansible.eda.webhook
```

Now, ansible-rulebook is ready and it's waiting for an event to match. If a webhook is triggered but the payload does not match our condition in our rule, we can see it in the ansible-rulebook verbose output:

```
…
INFO:root:Calling main in ansible.eda.webhook
INFO:aiohttp.access:127.0.0.1 [14/Oct/2022:09:49:32 +0000] "POST /endpoint HTTP/1.1" 200 158 "-" "curl/7.61.1"
INFO:root:Waiting for event
```

But once our payload matches what we are looking for, that's when the magic happens, so we will simulate a webhook with the correct payload:

```
curl -H 'Content-Type: application/json' -d "{\"message\": \"Ansible is super cool\"}" 127.0.0.1:5000/endpoint



INFO:root:Calling main in ansible.eda.webhook
INFO:aiohttp.access:127.0.0.1 [14/Oct/2022:09:50:28 +0000] "POST /endpoint HTTP/1.1" 200 158 "-" "curl/7.61.1"
INFO:root:calling Say Hello
INFO:root:call_action run_playbook
INFO:root:substitute_variables [{'name': 'say-what.yml'}] [{'event': {'payload': {'message': 'Ansible is super cool'}, 'meta': {'endpoint': 'endpoint', 'headers': {'Host': '127.0.0.1:5000', 'User-Agent': 'curl/7.61.1', 'Accept': '*/*', 'Content-Type': 'application/json', 'Content-Length': '36'}}}, 'fact': {'payload': {'message': 'Ansible is super cool'}, 'meta': {'endpoint': 'endpoint', 'headers': {'Host': '127.0.0.1:5000', 'User-Agent': 'curl/7.61.1', 'Accept': '*/*', 'Content-Type': 'application/json', 'Content-Length': '36'}}}}]
INFO:root:action args: {'name': 'say-what.yml'}
INFO:root:running Ansible playbook: say-what.yml
INFO:root:Calling Ansible runner

PLAY [say thanks] **************************************************************

TASK [debug] *******************************************************************
ok: [localhost] => {
    "msg": "Thank you, my friend!"
}

PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

INFO:root:Waiting for event

```

We can see from the output above, that the condition was met from the webhook and ansible-rulebook then triggered our action which was to run_playbook. The playbook we defined is then triggered and once it completes we can see we revert back to "Waiting for event".

Event-Driven Ansible opens up the possibilities of faster resolution and greater automated observation of our environments. It has the possibility of simplifying the lives of many technical and sleep-deprived engineers. The current `ansible-rulebook` is easy to learn and work with, and the graphical user interface `EDA-Server` will simplify this further.

[EDA Server](https://github.com/ansible/eda-server)

[Writing Rulebooks](https://www.youtube.com/watch?v=PtevBKX1SYI)

## Why Rulebooks?

Event-Driven Ansible contains a decision framework that was built using Drools. We need a rulebook to tell the system what events to flag and how to respond to them. These rulebooks are also created in YAML and are used like traditional Ansible Playbooks, so this makes it easier to understand and build the rulebooks we need. One key difference between playbooks and rulebooks is the If-this-then-that coding that is needed in a rulebook to make an event driven  automation approach work. The current ansible-rulebook is easy to learn and work with, and the graphical user interface EDA-Server will simplify this further.

### A rulebook is comprised of three main components:

- **Sources** define which event source we will use. These sources come from source plugins which have been built to accommodate common use cases. With time, more and more sources will be available. There are some source plugins that are available already, including: webhooks, Kafka, Azure service bus, file changes, and alertmanager.

- **Rules** define conditionals we will try to match from the event source. Should the condition be met, then we can trigger an action.

- **Actions** trigger what you need to happen should a condition be met. Some of the current actions are: run_playbook, run_module, set_fact, post_event, debug.

So to summarize:

**Events are processed by a rules engine**

- Rules trigger based on conditions and actions can be carried out by the rules engine
- Rules are organized into Ansible Rulebooks
- Ansible rules can apply to events occurring on specific  hosts or groups

**Conditional management of actions to events**

- Simple YAML structure for logical conditions
- Events can trigger different types of actions:
- Run Ansible Playbooks
- Run Modules directly
- Post new events to the event handler

**YAML-like format familiarity**

- Current Ansible users quickly learn and use Rulebook writing

## Other Resources

Whether you are beginning your automation journey or a seasoned veteran, there are a variety of resources to enhance your automation knowledge:

- [Self-paced lab exercises](https://www.redhat.com/en/engage/redhat-ansible-automation-202108061218) - We have interactive, in-browser exercises to help you get started with Event-Driven Ansible and ansible-rulebook.
- [Event-Driven Ansible web page](https://ansible.com/event-driven)
- [Introducing Event-Driven Ansible blog](https://www.ansible.com/blog/introducing-event-driven-ansible)
- [Why Event-Driven Matters](https://www.ansible.com/blog/why-event-driven-matters) - Have a look at another blog about why Event-Driven Ansible matters.
- [Event-Driven Rulebooks](https://youtu.be/PtevBKX1SYI) - Watch another example of Event-Driven Ansible on our YouTube channel.
- [EDA and Gitops](https://youtu.be/Bb51DftLbPE) - Watch another example of Event-Driven Ansible, but with GitOps, on our YouTube channel.
- Learn more about Event-Driven Ansible at our office hours [December 14, 2022](https://www.redhat.com/en/events/webinar/event-driven-ansible-office-hours-december).
- [Ansible Rulebook CLI](https://github.com/ansible/ansible-rulebook)
- [EDA Server](https://github.com/ansible/eda-server)

## Office Hours

Join us for Office Hours on the Event-Driven Ansible developer preview on December 14th at 11AM ET.  Get some tips and techniques, ask questions and share your feedback!  Learn from the community.  See you there.  [https://www.ansible.com/resources/webinars-training/event-driven-ansible-office-hours-dec](https://www.ansible.com/resources/webinars-training/event-driven-ansible-office-hours-dec)

## Providing Feedback

There are several ways you can give feedback - via comments/issue in here, on GitHub, the [Matrix chat](https://matrix.to/#/#eda:ansible.com), or via the event-driven-automation@redhat.com email.
