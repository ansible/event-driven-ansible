
.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. meta::
  :antsibull-docs: 2.12.0

.. Anchors

.. _ansible_collections.ansible.eda.activation_module:

.. Anchors: short name for ansible.builtin

.. Title

ansible.eda.activation module -- Manage rulebook activations in the EDA Controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 1.4.7).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

    To use it in a playbook, specify: :code:`ansible.eda.activation`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- This module allows the user to create or delete rulebook activations in the EDA Controller.


.. Aliases


.. Requirements






.. Options

Parameters
----------

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Parameter
    - Comments

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-awx_token_name"></div>
        <div class="ansibleOptionAnchor" id="parameter-awx_token"></div>
        <div class="ansibleOptionAnchor" id="parameter-token"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-awx_token:
      .. _ansible_collections.ansible.eda.activation_module__parameter-awx_token_name:
      .. _ansible_collections.ansible.eda.activation_module__parameter-token:

      .. rst-class:: ansible-option-title

      **awx_token_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-awx_token_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: awx_token, token`

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The token ID of the AWX controller.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-controller_host"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-controller_host:

      .. rst-class:: ansible-option-title

      **controller_host**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-controller_host" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      :ansible-option-versionadded:`added in ansible.eda 2.0.0`


      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The URL of the EDA controller.

      If not set, the value of the \ :literal:`CONTROLLER\_URL`\  environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-controller_password"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-controller_password:

      .. rst-class:: ansible-option-title

      **controller_password**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-controller_password" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      :ansible-option-versionadded:`added in ansible.eda 2.0.0`


      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Password used for authentication.

      If not set, the value of the \ :literal:`CONTROLLER\_PASSWORD`\  environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-controller_username"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-controller_username:

      .. rst-class:: ansible-option-title

      **controller_username**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-controller_username" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      :ansible-option-versionadded:`added in ansible.eda 2.0.0`


      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Username used for authentication.

      If not set, the value of the \ :literal:`CONTROLLER\_USERNAME`\  environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-decision_environment_name"></div>
        <div class="ansibleOptionAnchor" id="parameter-decision_environment"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-decision_environment:
      .. _ansible_collections.ansible.eda.activation_module__parameter-decision_environment_name:

      .. rst-class:: ansible-option-title

      **decision_environment_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-decision_environment_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: decision_environment`

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the decision environment associated with the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-description"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-description:

      .. rst-class:: ansible-option-title

      **description**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-description" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The description of the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-eda_credentials"></div>
        <div class="ansibleOptionAnchor" id="parameter-credentials"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-credentials:
      .. _ansible_collections.ansible.eda.activation_module__parameter-eda_credentials:

      .. rst-class:: ansible-option-title

      **eda_credentials**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-eda_credentials" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: credentials`

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A list of IDs for EDA credentials used by the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-enabled"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-enabled:

      .. rst-class:: ansible-option-title

      **enabled**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-enabled" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Whether the rulebook activation is enabled or not.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-event_streams"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-event_streams:

      .. rst-class:: ansible-option-title

      **event_streams**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-event_streams" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=integer`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A list of IDs representing the event streams that this rulebook activation listens to.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-extra_vars"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-extra_vars:

      .. rst-class:: ansible-option-title

      **extra_vars**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-extra_vars" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The extra variables for the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-k8s_service_name"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-k8s_service_name:

      .. rst-class:: ansible-option-title

      **k8s_service_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-k8s_service_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the Kubernetes service associated with this rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-log_level"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-log_level:

      .. rst-class:: ansible-option-title

      **log_level**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-log_level" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Allow setting the desired log level.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"debug"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"info"`
      - :ansible-option-choices-entry:`"error"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-name"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-name:

      .. rst-class:: ansible-option-title

      **name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-organization_name"></div>
        <div class="ansibleOptionAnchor" id="parameter-organization"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-organization:
      .. _ansible_collections.ansible.eda.activation_module__parameter-organization_name:

      .. rst-class:: ansible-option-title

      **organization_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-organization_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: organization`

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the organization.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-project_name"></div>
        <div class="ansibleOptionAnchor" id="parameter-project"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-project:
      .. _ansible_collections.ansible.eda.activation_module__parameter-project_name:

      .. rst-class:: ansible-option-title

      **project_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-project_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: project`

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the project associated with the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-request_timeout"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-request_timeout:

      .. rst-class:: ansible-option-title

      **request_timeout**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-request_timeout" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`float`

      :ansible-option-versionadded:`added in ansible.eda 2.0.0`


      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Timeout in seconds for the connection with the EDA controller.

      If not set, the value of the \ :literal:`CONTROLLER\_TIMEOUT`\  environment variable will be used.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`10.0`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-restart_policy"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-restart_policy:

      .. rst-class:: ansible-option-title

      **restart_policy**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-restart_policy" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The restart policy for the rulebook activation.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`"on-failure"`
      - :ansible-option-choices-entry-default:`"always"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"never"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-rulebook_name"></div>
        <div class="ansibleOptionAnchor" id="parameter-rulebook"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-rulebook:
      .. _ansible_collections.ansible.eda.activation_module__parameter-rulebook_name:

      .. rst-class:: ansible-option-title

      **rulebook_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-rulebook_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-aliases:`aliases: rulebook`

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the rulebook associated with the rulebook activation.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-state:

      .. rst-class:: ansible-option-title

      **state**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Desired state of the resource.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-swap_single_source"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-swap_single_source:

      .. rst-class:: ansible-option-title

      **swap_single_source**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-swap_single_source" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Allow swapping of single sources in a rulebook without name match.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-validate_certs"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-validate_certs:

      .. rst-class:: ansible-option-title

      **validate_certs**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-validate_certs" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      :ansible-option-versionadded:`added in ansible.eda 2.0.0`


      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Whether to allow insecure connections to Ansible Automation Platform EDA Controller instance.

      If \ :literal:`no`\ , SSL certificates will not be validated.

      This should only be used on personally controlled sites using self-signed certificates.

      If value not set, will try environment variable \ :literal:`CONTROLLER\_VERIFY\_SSL`\ 


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-webhooks"></div>

      .. _ansible_collections.ansible.eda.activation_module__parameter-webhooks:

      .. rst-class:: ansible-option-title

      **webhooks**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-webhooks" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A list of webhook IDs associated with the rulebook activation.


      .. raw:: html

        </div>


.. Attributes


.. Notes

Notes
-----

.. note::
   - Rulebook Activation API does not support PATCH method, due to this reason the module will not perform any modification when an existing rulebook activation is found.

.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    
    - name: Create a rulebook activation
      ansible.eda.activation:
        name: "Example Rulebook Activation"
        description: "Example Rulebook Activation description"
        project_name: "Example Project"
        rulebook_name: "hello_controller.yml"
        decision_environment_name: "Example Decision Environment"
        enabled: False
        awx_token_name: "Example Token"

    - name: Delete a rulebook activation
      ansible.eda.activation:
        name: "Example Rulebook Activation"
        state: absent




.. Facts


.. Return values

Return Values
-------------
Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this module:

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Key
    - Description

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-id"></div>

      .. _ansible_collections.ansible.eda.activation_module__return-id:

      .. rst-class:: ansible-option-title

      **id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-id" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`integer`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      ID of the rulebook activation.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when exists

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`37`


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Nikhil Jain (@jainnikhil30)
- Alina Buzachis (@alinabuzachis)



.. Extra links

Collection links
~~~~~~~~~~~~~~~~

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


.. Parsing errors

