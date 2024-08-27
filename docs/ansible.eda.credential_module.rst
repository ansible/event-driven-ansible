
.. Created with antsibull-docs 2.12.0

ansible.eda.credential module -- Manage credentials in EDA Controller
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 2.0.0-devel).

It is not included in ``ansible-core``.
To check whether it is installed, run ``ansible-galaxy collection list``.

To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

To use it in a playbook, specify: ``ansible.eda.credential``.

New in ansible.eda 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------

- This module allows the user to create, update or delete a credential in EDA controller.








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
      <div class="ansibleOptionAnchor" id="parameter-credential_type_name"></div>
      <p style="display: inline;"><strong>credential_type_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-credential_type_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the credential type.</p>
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
      <p>Description of the credential.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-inputs"></div>
      <p style="display: inline;"><strong>inputs</strong></p>
      <a class="ansibleOptionLink" href="#parameter-inputs" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">dictionary</span>
      </p>
    </td>
    <td valign="top">
      <p>Credential inputs where the keys are var names used in templating.</p>
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
      <p>Name of the credential.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-new_name"></div>
      <p style="display: inline;"><strong>new_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-new_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>Setting this option will change the existing name (lookup via name).</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-organization_name"></div>
      <div class="ansibleOptionAnchor" id="parameter-organization"></div>
      <p style="display: inline;"><strong>organization_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-organization_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: organization</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the organization.</p>
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

- \ `ansible.eda.credential <credential_module.rst>`__\  supports AAP 2.5 and onwards.


Examples
--------

.. code-block:: yaml

    
    - name: Create an EDA Credential
      ansible.eda.credential:
        name: "Example Credential"
        description: "Example credential description"
        inputs:
          field1: "field1"
        credential_type_name: "GitLab Personal Access Token"
        organization_name: Default

    - name: Delete an EDA Credential
      ansible.eda.credential:
        name: "Example Credential"
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
        <span style="color: purple;">integer</span>
      </p>
    </td>
    <td valign="top">
      <p>ID of the credential.</p>
      <p style="margin-top: 8px;"><b>Returned:</b> when exists</p>
      <p style="margin-top: 8px; color: blue; word-wrap: break-word; word-break: break-all;"><b style="color: black;">Sample:</b> <code>24</code></p>
    </td>
  </tr>
  </tbody>
  </table>




Authors
~~~~~~~

- Nikhil Jain (@jainnikhil30)
- Alina Buzachis (@alinabuzachis)



Collection links
~~~~~~~~~~~~~~~~

* `Issue Tracker <https://github.com/ansible/event-driven-ansible/issues>`__
* `Homepage <http://ansible.com/event-driven>`__
* `Repository (Sources) <https://github.com/ansible/event-driven-ansible>`__

