
.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. meta::
  :antsibull-docs: 2.12.0

.. Anchors

.. _ansible_collections.ansible.eda.user_module:

.. Anchors: short name for ansible.builtin

.. Title

ansible.eda.user module -- Manage users in EDA controller
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 1.4.7).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

    To use it in a playbook, specify: :code:`ansible.eda.user`.

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

- This module allows the user to create, update or delete users in a EDA controller.


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

      .. _ansible_collections.ansible.eda.user_module__parameter-controller_host:

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

      .. _ansible_collections.ansible.eda.user_module__parameter-controller_password:

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

      .. _ansible_collections.ansible.eda.user_module__parameter-controller_username:

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
        <div class="ansibleOptionAnchor" id="parameter-email"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-email:

      .. rst-class:: ansible-option-title

      **email**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-email" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Email address of the user.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-first_name"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-first_name:

      .. rst-class:: ansible-option-title

      **first_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-first_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      First name of the user.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-is_superuser"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-is_superuser:

      .. rst-class:: ansible-option-title

      **is_superuser**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-is_superuser" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Make user as superuser.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`false` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`true`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-last_name"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-last_name:

      .. rst-class:: ansible-option-title

      **last_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-last_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Last name of the user.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-new_username"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-new_username:

      .. rst-class:: ansible-option-title

      **new_username**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-new_username" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Setting this option will change the existing username.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-password:

      .. rst-class:: ansible-option-title

      **password**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-password" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Write-only field used to change the password.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-request_timeout"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-request_timeout:

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
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-state:

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
        <div class="ansibleOptionAnchor" id="parameter-update_secrets"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-update_secrets:

      .. rst-class:: ansible-option-title

      **update_secrets**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-update_secrets" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      \ :ansval:`true`\  will always change password if user specifies password, even if API gives $encrypted$ for password.

      \ :ansval:`false`\  will only set the password if other values change too.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-username:

      .. rst-class:: ansible-option-title

      **username**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-username" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name of the user.

      150 characters or fewer.

      Name can contain letters, digits and ('@', '.', '+', '-', '\_') only.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-validate_certs"></div>

      .. _ansible_collections.ansible.eda.user_module__parameter-validate_certs:

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


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    
    - name: Create EDA user
      ansible.eda.user:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        username: "test_collection_user"
        first_name: "Test Collection User"
        last_name: "Test Collection User"
        email: "test@test.com"
        password: "test"
        is_superuser: True
        state: present
      no_log: true

    - name: Delete user
      ansible.eda.user:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        username: "test_collection_user"
        state: absent

    - name: Update the username
      ansible.eda.user:
        username: "test_collection_user"
        new_username: "test_collection_user_updated"
        first_name: "Test Collection User"
        last_name: "Test Collection User"
        email: "test@test.com"
        password: "test"




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

      .. _ansible_collections.ansible.eda.user_module__return-id:

      .. rst-class:: ansible-option-title

      **id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-id" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      ID of the managed AWX token.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is 'present' and successful

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`"123"`


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Nikhil Jain (@jainnikhil30)
- Abhijeet Kasurde (@akasurde)



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

