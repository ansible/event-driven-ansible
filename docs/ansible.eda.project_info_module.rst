
.. Created with antsibull-docs 2.12.0

ansible.eda.project_info module -- List projects in EDA Controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 2.0.0-devel).

It is not included in ``ansible-core``.
To check whether it is installed, run ``ansible-galaxy collection list``.

To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

To use it in a playbook, specify: ``ansible.eda.project_info``.

New in ansible.eda 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------

- This module allows user to list project in a EDA controller.








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
      <div class="ansibleOptionAnchor" id="parameter-name"></div>
      <p style="display: inline;"><strong>name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the project.</p>
      <p>Return information about particular project available on EDA Controller.</p>
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






Examples
--------

.. code-block:: yaml


    - name: List a particular project
      ansible.eda.project_info:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        name: "Example"
        register: r

    - name: List all projects
      ansible.eda.project_info:
        controller_host: https://my_eda_host/
        controller_username: admin
        controller_password: MySuperSecretPassw0rd
        register: r





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
      <div class="ansibleOptionAnchor" id="return-projects"></div>
      <p style="display: inline;"><strong>projects</strong></p>
      <a class="ansibleOptionLink" href="#return-projects" title="Permalink to this return value"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">list</span>
        / <span style="color: purple;">elements=string</span>
      </p>
    </td>
    <td valign="top">
      <p>List of dicts containing information about projects</p>
      <p style="margin-top: 8px;"><b>Returned:</b> success</p>
      <p style="margin-top: 8px; color: blue; word-wrap: break-word; word-break: break-all;"><b style="color: black;">Sample:</b> <code>[{&#34;created_at&#34;: &#34;2024-08-12T20:35:28.367702Z&#34;, &#34;description&#34;: &#34;&#34;, &#34;eda_credential_id&#34;: null, &#34;git_hash&#34;: &#34;417b4dbe9b3472fd64212ef8233b865585e5ade3&#34;, &#34;id&#34;: 17, &#34;import_error&#34;: null, &#34;import_state&#34;: &#34;completed&#34;, &#34;modified_at&#34;: &#34;2024-08-12T20:35:28.367724Z&#34;, &#34;name&#34;: &#34;Sample Example Project&#34;, &#34;organization_id&#34;: 1, &#34;proxy&#34;: &#34;&#34;, &#34;scm_branch&#34;: &#34;&#34;, &#34;scm_refspec&#34;: &#34;&#34;, &#34;scm_type&#34;: &#34;git&#34;, &#34;signature_validation_credential_id&#34;: null, &#34;url&#34;: &#34;https://github.com/ansible/ansible-ui&#34;, &#34;verify_ssl&#34;: true}]</code></p>
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
