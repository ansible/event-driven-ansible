
.. Created with antsibull-docs 2.12.0

ansible.eda.activation_info module -- List rulebook activations in the EDA Controller
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 2.0.0-devel).

It is not included in ``ansible-core``.
To check whether it is installed, run ``ansible-galaxy collection list``.

To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

To use it in a playbook, specify: ``ansible.eda.activation_info``.

New in ansible.eda 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------

- List rulebook activations in the EDA controller.








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
      <p>The name of the rulebook activation.</p>
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


      - name: Get information about a rulebook activation
        ansible.eda.activation_info:
          name: "Example Rulebook Activation"

      - name: List all rulebook activations
        ansible.eda.activation_info:





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
      <div class="ansibleOptionAnchor" id="return-activations"></div>
      <p style="display: inline;"><strong>activations</strong></p>
      <a class="ansibleOptionLink" href="#return-activations" title="Permalink to this return value"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">list</span>
        / <span style="color: purple;">elements=dictionary</span>
      </p>
    </td>
    <td valign="top">
      <p>Information about rulebook activations.</p>
      <p style="margin-top: 8px;"><b>Returned:</b> always</p>
      <p style="margin-top: 8px; color: blue; word-wrap: break-word; word-break: break-all;"><b style="color: black;">Sample:</b> <code>[{&#34;awx_token_id&#34;: 1, &#34;created_at&#34;: &#34;2024-08-10T14:22:30.123Z&#34;, &#34;current_job_id&#34;: &#34;2&#34;, &#34;decision_environment_id&#34;: 1, &#34;description&#34;: &#34;A test activation&#34;, &#34;eda_credentials&#34;: [], &#34;event_streams&#34;: [], &#34;extra_var&#34;: &#34;&#34;, &#34;id&#34;: 1, &#34;is_enabled&#34;: true, &#34;k8s_service_name&#34;: &#34;&#34;, &#34;log_level&#34;: &#34;info&#34;, &#34;modified_at&#34;: &#34;2024-08-15T11:45:00.987Z&#34;, &#34;name&#34;: &#34;Test activation&#34;, &#34;organization_id&#34;: 1, &#34;project_id&#34;: 2, &#34;restart_count&#34;: 2, &#34;restart_policy&#34;: &#34;on-failure&#34;, &#34;rulebook_id&#34;: 1, &#34;rulebook_name&#34;: &#34;Test rulebook&#34;, &#34;rules_count&#34;: 2, &#34;rules_fired_count&#34;: 2, &#34;status&#34;: &#34;running&#34;, &#34;status_message&#34;: &#34;Activation is running successfully.&#34;, &#34;swap_single_source&#34;: false, &#34;webhooks&#34;: []}]</code></p>
    </td>
  </tr>
  </tbody>
  </table>




Authors
~~~~~~~

- Alina Buzachis (@alinabuzachis)



Collection links
~~~~~~~~~~~~~~~~

* `Issue Tracker <https://github.com/ansible/event-driven-ansible/issues>`__
* `Homepage <http://ansible.com/event-driven>`__
* `Repository (Sources) <https://github.com/ansible/event-driven-ansible>`__
