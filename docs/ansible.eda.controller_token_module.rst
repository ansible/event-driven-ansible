
.. Created with antsibull-docs 2.12.0

ansible.eda.controller_token module -- Manage AWX tokens in EDA controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 2.0.0-devel).

It is not included in ``ansible-core``.
To check whether it is installed, run ``ansible-galaxy collection list``.

To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

To use it in a playbook, specify: ``ansible.eda.controller_token``.

New in ansible.eda 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------

- This module allows the user to manage AWX tokens in a EDA controller.








Parameters
----------

.. raw:: html

  <table style="width: 100%;">
  <thead>
    <tr>
    <th><p>Parameter</p></th>
    <th><p>Comments</p></th>
  </tr>
  </thead>
  <tbody>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-controller_host"></div>
      <p style="display: inline;"><strong>controller_host</strong></p>
      <a class="ansibleOptionLink" href="#parameter-controller_host" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
        / <span style="color: red;">required</span>
      </p>
      <p><i style="font-size: small; color: darkgreen;">added in ansible.eda 2.0.0</i></p>
    </td>
    <td valign="top">
      <p>The URL of the EDA controller.</p>
      <p>If not set, the value of the <code class='docutils literal notranslate'>CONTROLLER_URL</code> environment variable will be used.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-controller_password"></div>
      <p style="display: inline;"><strong>controller_password</strong></p>
      <a class="ansibleOptionLink" href="#parameter-controller_password" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
      <p><i style="font-size: small; color: darkgreen;">added in ansible.eda 2.0.0</i></p>
    </td>
    <td valign="top">
      <p>Password used for authentication.</p>
      <p>If not set, the value of the <code class='docutils literal notranslate'>CONTROLLER_PASSWORD</code> environment variable will be used.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-controller_username"></div>
      <p style="display: inline;"><strong>controller_username</strong></p>
      <a class="ansibleOptionLink" href="#parameter-controller_username" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
      <p><i style="font-size: small; color: darkgreen;">added in ansible.eda 2.0.0</i></p>
    </td>
    <td valign="top">
      <p>Username used for authentication.</p>
      <p>If not set, the value of the <code class='docutils literal notranslate'>CONTROLLER_USERNAME</code> environment variable will be used.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-description"></div>
      <p style="display: inline;"><strong>description</strong></p>
      <a class="ansibleOptionLink" href="#parameter-description" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The description of the project.</p>
      <p>Required when <code class="ansible-option-value literal notranslate"><a class="reference internal" href="#parameter-state"><span class="std std-ref"><span class="pre">state=present</span></span></a></code>.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-name"></div>
      <p style="display: inline;"><strong>name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
        / <span style="color: red;">required</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the AWX token.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-request_timeout"></div>
      <p style="display: inline;"><strong>request_timeout</strong></p>
      <a class="ansibleOptionLink" href="#parameter-request_timeout" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">float</span>
      </p>
      <p><i style="font-size: small; color: darkgreen;">added in ansible.eda 2.0.0</i></p>
    </td>
    <td valign="top">
      <p>Timeout in seconds for the connection with the EDA controller.</p>
      <p>If not set, the value of the <code class='docutils literal notranslate'>CONTROLLER_TIMEOUT</code> environment variable will be used.</p>
      <p style="margin-top: 8px;"><b style="color: blue;">Default:</b> <code style="color: blue;">10.0</code></p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-state"></div>
      <p style="display: inline;"><strong>state</strong></p>
      <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>Desired state of the resource.</p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code style="color: blue;"><b>&#34;present&#34;</b></code> <span style="color: blue;">← (default)</span></p></li>
        <li><p><code>&#34;absent&#34;</code></p></li>
      </ul>

    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-token"></div>
      <p style="display: inline;"><strong>token</strong></p>
      <a class="ansibleOptionLink" href="#parameter-token" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The AWX token value.</p>
      <p>Required when <code class="ansible-option-value literal notranslate"><a class="reference internal" href="#parameter-state"><span class="std std-ref"><span class="pre">state=present</span></span></a></code>.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-validate_certs"></div>
      <p style="display: inline;"><strong>validate_certs</strong></p>
      <a class="ansibleOptionLink" href="#parameter-validate_certs" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">boolean</span>
      </p>
      <p><i style="font-size: small; color: darkgreen;">added in ansible.eda 2.0.0</i></p>
    </td>
    <td valign="top">
      <p>Whether to allow insecure connections to Ansible Automation Platform EDA Controller instance.</p>
      <p>If <code class='docutils literal notranslate'>no</code>, SSL certificates will not be validated.</p>
      <p>This should only be used on personally controlled sites using self-signed certificates.</p>
      <p>If value not set, will try environment variable <code class='docutils literal notranslate'>CONTROLLER_VERIFY_SSL</code></p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code>false</code></p></li>
        <li><p><code style="color: blue;"><b>true</b></code> <span style="color: blue;">← (default)</span></p></li>
      </ul>

    </td>
  </tr>
  </tbody>
  </table>




Notes
-----

- Controller Token API does not support PATCH method, due to this reason the module deletes and re-creates the token when existing controller token is found. This will cause module to report changed, every time update is called.


Examples
--------

.. code-block:: yaml

    
    - name: Create AWX token
      ansible.eda.controller_token:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        name: "Example AWX token"
        description: "Example AWX token description"
        token: "<TOKEN_VALUE>"
        state: present
      no_log: true

    - name: Delete AWX token
      ansible.eda.controller_token:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        name: "Example AWX token"
        state: absent





Return Values
-------------
The following are the fields unique to this module:

.. raw:: html

  <table style="width: 100%;">
  <thead>
    <tr>
    <th><p>Key</p></th>
    <th><p>Description</p></th>
  </tr>
  </thead>
  <tbody>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="return-id"></div>
      <p style="display: inline;"><strong>id</strong></p>
      <a class="ansibleOptionLink" href="#return-id" title="Permalink to this return value"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>ID of the managed AWX token.</p>
      <p style="margin-top: 8px;"><b>Returned:</b> when state is &#x27;present&#x27; and successful</p>
      <p style="margin-top: 8px; color: blue; word-wrap: break-word; word-break: break-all;"><b style="color: black;">Sample:</b> <code>&#34;123&#34;</code></p>
    </td>
  </tr>
  </tbody>
  </table>




Authors
~~~~~~~

- Abhijeet Kasurde (@akasurde)



Collection links
~~~~~~~~~~~~~~~~

* `Issue Tracker <https://github.com/ansible/event-driven-ansible/issues>`__
* `Homepage <http://ansible.com/event-driven>`__
* `Repository (Sources) <https://github.com/ansible/event-driven-ansible>`__

