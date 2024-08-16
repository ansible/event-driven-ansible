.. _ansible.eda.activation_info_module:


***************************
ansible.eda.activation_info
***************************

**List rulebook activations in the EDA Controller**


Version added: 2.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- List rulebook activations in the EDA controller.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>controller_host</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The URL of the EDA controller.</div>
                        <div>If not set, the value of the <code>CONTROLLER_URL</code> environment variable will be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>controller_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>Password used for authentication.</div>
                        <div>If not set, the value of the <code>CONTROLLER_PASSWORD</code> environment variable will be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>controller_username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>Username used for authentication.</div>
                        <div>If not set, the value of the <code>CONTROLLER_USERNAME</code> environment variable will be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The name of the rulebook activation.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>request_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">float</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">10</div>
                </td>
                <td>
                        <div>Timeout in seconds for the connection with the EDA controller.</div>
                        <div>If not set, the value of the <code>CONTROLLER_TIMEOUT</code> environment variable will be used.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_certs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Whether to allow insecure connections to Ansible Automation Platform EDA Controller instance.</div>
                        <div>If <code>no</code>, SSL certificates will not be validated.</div>
                        <div>This should only be used on personally controlled sites using self-signed certificates.</div>
                        <div>If value not set, will try environment variable <code>CONTROLLER_VERIFY_SSL</code></div>
                </td>
            </tr>
    </table>
    <br/>




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
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>activations</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Information about rulebook activations.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;id&#x27;: 1, &#x27;name&#x27;: &#x27;Test activation&#x27;, &#x27;description&#x27;: &#x27;A test activation&#x27;, &#x27;is_enabled&#x27;: True, &#x27;status&#x27;: &#x27;running&#x27;, &#x27;extra_var&#x27;: &#x27;&#x27;, &#x27;decision_environment_id&#x27;: 1, &#x27;project_id&#x27;: 2, &#x27;rulebook_id&#x27;: 1, &#x27;organization_id&#x27;: 1, &#x27;restart_policy&#x27;: &#x27;on-failure&#x27;, &#x27;restart_count&#x27;: 2, &#x27;rulebook_name&#x27;: &#x27;Test rulebook&#x27;, &#x27;current_job_id&#x27;: &#x27;2&#x27;, &#x27;rules_count&#x27;: 2, &#x27;rules_fired_count&#x27;: 2, &#x27;created_at&#x27;: &#x27;2024-08-10T14:22:30.123Z&#x27;, &#x27;modified_at&#x27;: &#x27;2024-08-15T11:45:00.987Z&#x27;, &#x27;status_message&#x27;: &#x27;Activation is running successfully.&#x27;, &#x27;awx_token_id&#x27;: 1, &#x27;event_streams&#x27;: [], &#x27;log_level&#x27;: &#x27;info&#x27;, &#x27;eda_credentials&#x27;: [], &#x27;k8s_service_name&#x27;: &#x27;&#x27;, &#x27;webhooks&#x27;: [], &#x27;swap_single_source&#x27;: False}]</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Alina Buzachis (@alinabuzachis)
