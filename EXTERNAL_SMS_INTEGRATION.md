# External SMS Integration for Ansible EDA Collection

This document describes the implementation of External Secret Management System (SMS) integration in the Ansible EDA Collection, corresponding to the functionality added in eda-server commit 1766604.

## Overview

The External SMS integration allows EDA credential fields to be linked to external secret management systems like HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, and others. This enhances security by centralizing secret storage and eliminating hardcoded credentials.

## New Modules Added

### 1. `credential_input_source`
**Purpose**: Manage credential input sources that link credential fields to external SMS.

**Key Features**:
- Create/update/delete credential input sources
- Link target credentials (regular) to source credentials (external SMS)
- Configure metadata for secret retrieval
- Support for all 10 SMS providers from awx-plugins-core

**Example Usage**:
```yaml
- name: Link password field to HashiCorp Vault
  ansible.eda.credential_input_source:
    target_credential_name: "MyAppCredential"
    source_credential_name: "HashiCorpVaultCred"
    input_field_name: "password"
    description: "Password from Vault"
    metadata:
      secret_path: "secret/myapp"
      secret_key: "password"
    organization_name: "Default"
    state: present
```

### 2. `credential_input_source_info`
**Purpose**: List and query credential input sources.

**Key Features**:
- List all input sources or filter by various criteria
- Filter by target credential, source credential, field name, or organization
- Returns detailed information about each input source

**Example Usage**:
```yaml
- name: List all input sources for a credential
  ansible.eda.credential_input_source_info:
    target_credential_name: "MyAppCredential"
```

### 3. `credential_test`
**Purpose**: Test credential connectivity, especially for external SMS credentials.

**Key Features**:
- Validate credential connectivity to external systems
- Test secret retrieval without modifying data
- Support for testing with specific metadata

**Example Usage**:
```yaml
- name: Test HashiCorp Vault credential
  ansible.eda.credential_test:
    name: "HashiCorpVaultCred"
    organization_name: "Default"
```

### 4. `credential_type_test`
**Purpose**: Test credential type configuration for external SMS.

**Key Features**:
- Validate credential type setup
- Test with sample inputs
- Verify external SMS integration capability

**Example Usage**:
```yaml
- name: Test credential type configuration
  ansible.eda.credential_type_test:
    name: "HashiCorp Vault Secret Lookup"
    inputs:
      url: "https://vault.example.com:8200"
      token: "hvs.test-token"
```

## Supported External SMS Providers

The integration supports 10 external SMS providers via awx-plugins-core:

1. **CyberArk Central Credential Provider Lookup** (`credentials-aim`)
2. **AWS Secrets Manager lookup** (`credentials-aws-secretsmanager-credential`)
3. **Microsoft Azure Key Vault** (`credentials-azure-kv`)
4. **Centrify Vault Credential Provider Lookup** (`credentials-centrify-vault-kv`)
5. **CyberArk Conjur Secrets Manager Lookup** (`credentials-conjur`)
6. **HashiCorp Vault Secret Lookup** (`credentials-hashivault-kv`)
7. **HashiCorp Vault Signed SSH** (`credentials-hashivault-ssh`)
8. **Thycotic DevOps Secrets Vault** (`credentials-thycotic-dsv`)
9. **Thycotic Secret Server** (`credentials-thycotic-tss`)
10. **GitHub App Installation Access Token Lookup** (`credentials-github-app`)

## Integration Tests

Comprehensive integration tests are provided in `tests/integration/targets/credential_input_source/tasks/main.yml` that cover:

- **CRUD Operations**: Create, update, delete credential input sources
- **Error Handling**: Invalid credentials, missing parameters, etc.
- **Check Mode**: Validate changes without applying them
- **Info Queries**: Test filtering and listing functionality
- **Connectivity Testing**: Test credential and credential type validation
- **Cleanup**: Proper resource cleanup in all scenarios

## API Endpoints Used

The modules interact with the following EDA Controller API endpoints (added in commit 1766604):

- `GET/POST /api/eda/v1/credential-input-sources/` - CRUD operations
- `GET /api/eda/v1/eda-credentials/{id}/input_sources/` - List input sources for a credential
- `POST /api/eda/v1/eda-credentials/{id}/test/` - Test credential connectivity
- `POST /api/eda/v1/credential-types/{id}/test/` - Test credential type configuration

## Workflow Example

Here's a complete workflow for setting up External SMS with HashiCorp Vault:

```yaml
---
- name: Configure External SMS Integration
  hosts: localhost
  tasks:
    # 1. Create external SMS credential
    - name: Create HashiCorp Vault credential
      ansible.eda.credential:
        name: "ProductionVault"
        description: "Production HashiCorp Vault"
        credential_type_name: "HashiCorp Vault Secret Lookup"
        inputs:
          url: "https://vault.company.com:8200"
          token: "hvs.production-token"
          cacert: "{{ vault_ca_cert }}"
        organization_name: "Production"
        state: present

    # 2. Test the external credential
    - name: Test Vault connectivity
      ansible.eda.credential_test:
        name: "ProductionVault"
        organization_name: "Production"

    # 3. Create target credential with placeholder values
    - name: Create application credential
      ansible.eda.credential:
        name: "WebAppCredential"
        description: "Web application database credentials"
        credential_type_name: "Machine"
        inputs:
          username: "webapp"
          password: "placeholder"  # Will be replaced by Vault
        organization_name: "Production"
        state: present

    # 4. Link password field to Vault
    - name: Link password to Vault secret
      ansible.eda.credential_input_source:
        target_credential_name: "WebAppCredential"
        source_credential_name: "ProductionVault"
        input_field_name: "password"
        description: "Database password from Vault"
        metadata:
          secret_path: "secret/webapp/database"
          secret_key: "password"
        organization_name: "Production"
        state: present

    # 5. Verify the configuration
    - name: List input sources for verification
      ansible.eda.credential_input_source_info:
        target_credential_name: "WebAppCredential"
      register: input_sources

    - name: Display configuration
      debug:
        msg: "Configured {{ input_sources.credential_input_sources | length }} input sources"
```

## Security Benefits

1. **Centralized Secret Management**: Secrets stored in dedicated SMS rather than EDA database
2. **Dynamic Secret Retrieval**: Secrets fetched at runtime, not stored statically
3. **Audit Trail**: External SMS provides comprehensive audit logs
4. **Secret Rotation**: Automatic support for secret rotation in external systems
5. **Access Control**: Fine-grained access control via SMS RBAC systems

## Compatibility

- **EDA Server**: Requires EDA Server with commit 1766604 or later
- **AAP Version**: Supports AAP 2.5 and onwards
- **Python**: Requires Python 3.9 or greater
- **Dependencies**: Uses awx-plugins-core for SMS connectivity

## Testing

Run the integration tests with:

```bash
# Test the new credential input source functionality
ansible-test integration credential_input_source

# Test in a development environment
tox -e integration -- tests/integration/targets/credential_input_source/
```

## Migration Guide

To migrate existing hardcoded credentials to External SMS:

1. Set up your external SMS (HashiCorp Vault, etc.)
2. Create SMS credential in EDA using appropriate credential type
3. Test SMS connectivity using `credential_test` module
4. Create credential input sources to link existing credentials to SMS
5. Verify functionality in non-production environment
6. Update production credentials to use External SMS

This implementation provides a complete External SMS integration that follows the collection's established patterns while enabling enterprise-grade secret management for EDA automation.