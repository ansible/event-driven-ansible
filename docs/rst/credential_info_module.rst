.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. meta::
  :antsibull-docs: 2.13.0

.. Anchors

.. _ansible_collections.ansible.eda.credential_info_module:

.. Anchors: short name for ansible.builtin

.. Title

ansible.eda.credential_info module -- List credentials in the EDA Controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 1.4.7).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

    To use it in a playbook, specify: :code:`ansible.eda.credential_info`.

.. version_added

.. rst-class:: ansible-version-added

New in ansible.eda 2.0.0

.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- List credentials in the EDA controller.


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
        <div class="ansibleOptionAnchor" id="parameter-controller_host"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-controller_host:

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

      If not set, the value of the :literal:`CONTROLLER\_URL` environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-controller_password"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-controller_password:

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

      If not set, the value of the :literal:`CONTROLLER\_PASSWORD` environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-controller_username"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-controller_username:

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

      If not set, the value of the :literal:`CONTROLLER\_USERNAME` environment variable will be used.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-name"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-name:

      .. rst-class:: ansible-option-title

      **name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the credential.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-request_timeout"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-request_timeout:

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

      If not set, the value of the :literal:`CONTROLLER\_TIMEOUT` environment variable will be used.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`10.0`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-validate_certs"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__parameter-validate_certs:

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

      If :literal:`no`\ , SSL certificates will not be validated.

      This should only be used on personally controlled sites using self-signed certificates.

      If value not set, will try environment variable :literal:`CONTROLLER\_VERIFY\_SSL`


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    - name: Get information about a credential
      ansible.eda.credential_info:
        name: "Test"

    - name: List all credentials
      ansible.eda.credential_info:



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
        <div class="ansibleOptionAnchor" id="return-credentials"></div>

      .. _ansible_collections.ansible.eda.credential_info_module__return-credentials:

      .. rst-class:: ansible-option-title

      **credentials**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-credentials" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Information about credentials.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`[{"created\_at": "2024-08-14T08:57:55.151787Z", "credential\_type": {"id": 1, "kind": "scm", "name": "Source Control", "namespace": "scm"}, "description": "This is a test credential", "id": 24, "inputs": {"password": "$encrypted$", "username": "testuser"}, "managed": false, "modified\_at": "2024-08-14T08:57:56.324925Z", "name": "New Test Credential", "organization": {"description": "The default organization", "id": 1, "name": "Default"}, "references": null}]`


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

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
