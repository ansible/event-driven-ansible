install_ansible_rulebook
=========

A role to install the ansible-rulebook CLI. For more information please see the following Github repositories:

- [Event-Driven Ansible](https://github.com/ansible/event-driven-ansible)
- [ansible-rulebook](https://github.com/ansible/ansible-rulebook)

Requirements
------------

Some tasks in this role require [privilege escalation](https://docs.ansible.com/ansible/latest/plugins/become.html) and therefore you may need to provide the necessary credentials.

Example Playbook
----------------

- name: Install ansible-rulebook
  hosts: all
  gather_facts: true
  roles:
    - install_ansible_rulebook

License
-------

Apache License 2.0
