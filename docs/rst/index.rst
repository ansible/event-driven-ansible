

.. meta::
  :antsibull-docs: 2.12.0


.. _plugins_in_ansible.eda:

Ansible.Eda
===========

Collection version 1.4.7

.. contents::
   :local:
   :depth: 1

Description
-----------

Event-Driven Ansible

**Authors:**

* bthomass@redhat.com
* jpisciot@redhat.com

**Supported ansible-core versions:**

* 2.15.0 or newer

.. ansible-links::

  - title: "Issue Tracker"
    url: "https://github.com/ansible/event-driven-ansible/issues"
    external: true
  - title: "Homepage"
    url: "http://ansible.com/event-driven"
    external: true
  - title: "Repository (Sources)"
    url: "https://github.com/ansible/event-driven-ansible"
    external: true




.. toctree::
    :maxdepth: 1

Plugin Index
------------

These are the plugins in the ansible.eda collection:


Modules
~~~~~~~

* :ansplugin:`activation module <ansible.eda.activation#module>` -- Manage rulebook activations in the EDA Controller
* :ansplugin:`activation_info module <ansible.eda.activation_info#module>` -- List rulebook activations in the EDA Controller
* :ansplugin:`controller_token module <ansible.eda.controller_token#module>` -- Manage AWX tokens in EDA controller
* :ansplugin:`credential module <ansible.eda.credential#module>` -- Manage credentials in EDA Controller
* :ansplugin:`credential_info module <ansible.eda.credential_info#module>` -- List credentials in the EDA Controller
* :ansplugin:`credential_type module <ansible.eda.credential_type#module>` -- Manage credential types in EDA Controller
* :ansplugin:`credential_type_info module <ansible.eda.credential_type_info#module>` -- List credential types in EDA Controller
* :ansplugin:`decision_environment module <ansible.eda.decision_environment#module>` -- Create, update or delete decision environment in EDA Controller
* :ansplugin:`decision_environment_info module <ansible.eda.decision_environment_info#module>` -- List a decision environment in EDA Controller
* :ansplugin:`project module <ansible.eda.project#module>` -- Create, update or delete project in EDA Controller
* :ansplugin:`project_info module <ansible.eda.project_info#module>` -- List projects in EDA Controller
* :ansplugin:`user module <ansible.eda.user#module>` -- Manage users in EDA controller

.. toctree::
    :maxdepth: 1
    :hidden:

    activation_module
    activation_info_module
    controller_token_module
    credential_module
    credential_info_module
    credential_type_module
    credential_type_info_module
    decision_environment_module
    decision_environment_info_module
    project_module
    project_info_module
    user_module
