
.. Created with antsibull-docs 2.12.0

ansible.eda.activation module -- Manage rulebook activations in the EDA Controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This module is part of the `ansible.eda collection <https://galaxy.ansible.com/ui/repo/published/ansible/eda/>`_ (version 2.0.0-devel).

It is not included in ``ansible-core``.
To check whether it is installed, run ``ansible-galaxy collection list``.

To install it, use: :code:`ansible-galaxy collection install ansible.eda`.

To use it in a playbook, specify: ``ansible.eda.activation``.


.. contents::
   :local:
   :depth: 1


Synopsis
--------

- This module allows the user to create or delete rulebook activations in the EDA Controller.








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
      <div class="ansibleOptionAnchor" id="parameter-awx_token_name"></div>
      <div class="ansibleOptionAnchor" id="parameter-awx_token"></div>
      <div class="ansibleOptionAnchor" id="parameter-token"></div>
      <p style="display: inline;"><strong>awx_token_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-awx_token_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: awx_token, token</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The token ID of the AWX controller.</p>
    </td>
  </tr>
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
      <div class="ansibleOptionAnchor" id="parameter-decision_environment_name"></div>
      <div class="ansibleOptionAnchor" id="parameter-decision_environment"></div>
      <p style="display: inline;"><strong>decision_environment_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-decision_environment_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: decision_environment</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the decision environment associated with the rulebook activation.</p>
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
      <p>The description of the rulebook activation.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-eda_credentials"></div>
      <div class="ansibleOptionAnchor" id="parameter-credentials"></div>
      <p style="display: inline;"><strong>eda_credentials</strong></p>
      <a class="ansibleOptionLink" href="#parameter-eda_credentials" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: credentials</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">list</span>
        / <span style="color: purple;">elements=string</span>
      </p>
    </td>
    <td valign="top">
      <p>A list of IDs for EDA credentials used by the rulebook activation.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-enabled"></div>
      <p style="display: inline;"><strong>enabled</strong></p>
      <a class="ansibleOptionLink" href="#parameter-enabled" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">boolean</span>
      </p>
    </td>
    <td valign="top">
      <p>Whether the rulebook activation is enabled or not.</p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code>false</code></p></li>
        <li><p><code style="color: blue;"><b>true</b></code> <span style="color: blue;">← (default)</span></p></li>
      </ul>

    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-event_streams"></div>
      <p style="display: inline;"><strong>event_streams</strong></p>
      <a class="ansibleOptionLink" href="#parameter-event_streams" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">list</span>
        / <span style="color: purple;">elements=integer</span>
      </p>
    </td>
    <td valign="top">
      <p>A list of IDs representing the event streams that this rulebook activation listens to.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-extra_vars"></div>
      <p style="display: inline;"><strong>extra_vars</strong></p>
      <a class="ansibleOptionLink" href="#parameter-extra_vars" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The extra variables for the rulebook activation.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-k8s_service_name"></div>
      <p style="display: inline;"><strong>k8s_service_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-k8s_service_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the Kubernetes service associated with this rulebook activation.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-log_level"></div>
      <p style="display: inline;"><strong>log_level</strong></p>
      <a class="ansibleOptionLink" href="#parameter-log_level" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>Allow setting the desired log level.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code style="color: blue;"><b>&#34;debug&#34;</b></code> <span style="color: blue;">← (default)</span></p></li>
        <li><p><code>&#34;info&#34;</code></p></li>
        <li><p><code>&#34;error&#34;</code></p></li>
      </ul>

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
      <p>The name of the rulebook activation.</p>
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
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-project_name"></div>
      <div class="ansibleOptionAnchor" id="parameter-project"></div>
      <p style="display: inline;"><strong>project_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-project_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: project</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the project associated with the rulebook activation.</p>
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
      <div class="ansibleOptionAnchor" id="parameter-restart_policy"></div>
      <p style="display: inline;"><strong>restart_policy</strong></p>
      <a class="ansibleOptionLink" href="#parameter-restart_policy" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The restart policy for the rulebook activation.</p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code>&#34;on-failure&#34;</code></p></li>
        <li><p><code style="color: blue;"><b>&#34;always&#34;</b></code> <span style="color: blue;">← (default)</span></p></li>
        <li><p><code>&#34;never&#34;</code></p></li>
      </ul>

    </td>
  </tr>
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-rulebook_name"></div>
      <div class="ansibleOptionAnchor" id="parameter-rulebook"></div>
      <p style="display: inline;"><strong>rulebook_name</strong></p>
      <a class="ansibleOptionLink" href="#parameter-rulebook_name" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;"><span style="color: darkgreen; white-space: normal;">aliases: rulebook</span></p>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">string</span>
      </p>
    </td>
    <td valign="top">
      <p>The name of the rulebook associated with the rulebook activation.</p>
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
      <div class="ansibleOptionAnchor" id="parameter-swap_single_source"></div>
      <p style="display: inline;"><strong>swap_single_source</strong></p>
      <a class="ansibleOptionLink" href="#parameter-swap_single_source" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">boolean</span>
      </p>
    </td>
    <td valign="top">
      <p>Allow swapping of single sources in a rulebook without name match.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
      <p style="margin-top: 8px;"><b">Choices:</b></p>
      <ul>
        <li><p><code>false</code></p></li>
        <li><p><code style="color: blue;"><b>true</b></code> <span style="color: blue;">← (default)</span></p></li>
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
  <tr>
    <td valign="top">
      <div class="ansibleOptionAnchor" id="parameter-webhooks"></div>
      <p style="display: inline;"><strong>webhooks</strong></p>
      <a class="ansibleOptionLink" href="#parameter-webhooks" title="Permalink to this option"></a>
      <p style="font-size: small; margin-bottom: 0;">
        <span style="color: purple;">list</span>
        / <span style="color: purple;">elements=string</span>
      </p>
    </td>
    <td valign="top">
      <p>A list of webhook IDs associated with the rulebook activation.</p>
      <p>This parameter is supported in AAP 2.5 and onwards. If specified for AAP 2.4, value will be ignored.</p>
    </td>
  </tr>
  </tbody>
  </table>




Notes
-----

- Rulebook Activation API does not support PATCH method, due to this reason the module will not perform any modification when an existing rulebook activation is found.


Examples
--------

.. code-block:: yaml

    
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
      <p>ID of the rulebook activation.</p>
      <p style="margin-top: 8px;"><b>Returned:</b> when exists</p>
      <p style="margin-top: 8px; color: blue; word-wrap: break-word; word-break: break-all;"><b style="color: black;">Sample:</b> <code>37</code></p>
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

