.. _gateway_authentication:

************************************
Gateway Authentication Requirements
************************************

.. contents::
   :local:

Overview
========

Starting with AAP 2.5, the Ansible Automation Platform Gateway serves as the
single entry point for all AAP services, including EDA Controller. When using
the ``ansible.eda`` collection through Gateway, **only OAuth token
authentication is supported**. Basic auth (username/password) does not work
through Gateway.

When connecting directly to EDA Controller (bypassing Gateway), both basic auth
and token auth continue to work.

Design Decision
===============

Token-only authentication through Gateway is the intended design, not a
limitation to be fixed. Gateway uses OAuth2 for authentication and does not
proxy basic auth credentials to downstream services. This aligns with security
best practices by avoiding credential forwarding between services.

The ``ansible.eda`` collection will not add basic auth support for Gateway
connections. Users should use OAuth tokens when connecting through Gateway.

Generating a Token
==================

**Via the AAP UI:**

1. Log in to the AAP Gateway UI.
2. Navigate to your user profile (top right corner).
3. Select **Tokens**.
4. Click **Create Token**.
5. Choose the appropriate scope and save.
6. Copy the token value (it is only shown once).

**Via the API:**

.. code-block:: bash

   curl -X POST https://aap-gateway.example.com/api/gateway/v1/tokens/ \
     -H "Content-Type: application/json" \
     -u "admin:password" \
     -d '{"scope": "write"}'

The response includes the ``token`` field with the OAuth token value.

Using Token Authentication
==========================

Set the ``aap_token`` parameter (or the ``AAP_TOKEN`` environment variable)
instead of ``aap_username`` and ``aap_password``:

.. code-block:: yaml

   - name: Manage EDA resources via Gateway
     hosts: localhost
     connection: local
     gather_facts: false
     module_defaults:
       group/ansible.eda.eda:
         aap_hostname: "https://aap-gateway.example.com"
         aap_token: "{{ vault_aap_token }}"
         aap_validate_certs: true
     tasks:
       - name: Create a project
         ansible.eda.project:
           organization_name: Default
           name: My Project
           url: https://github.com/ansible/eda-sample-project

Or using environment variables:

.. code-block:: bash

   export AAP_HOSTNAME=https://aap-gateway.example.com
   export AAP_TOKEN=your-oauth-token
   ansible-playbook my-eda-playbook.yml

Troubleshooting
===============

**"HTTP Error 401: Unauthorized" when using username/password through Gateway**

Gateway does not support basic auth. Switch to token authentication:

1. Generate a token (see above).
2. Replace ``aap_username`` and ``aap_password`` with ``aap_token``.
3. Remove any ``CONTROLLER_USERNAME``/``CONTROLLER_PASSWORD`` or
   ``AAP_USERNAME``/``AAP_PASSWORD`` environment variables.

**"HTTP Error 401: Unauthorized" when using a token**

Verify the token is valid and has not expired. Generate a new token if needed.
Ensure you are using the Gateway URL, not the direct EDA Controller URL.
