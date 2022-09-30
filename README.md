# Ansible Collection - benthomasson.eda

Documentation for the collection.

# Integration tests

Currently integration tests require [docker](https://docs.docker.com/engine/install/)/[podman](https://podman.io/getting-started/installation) and [docker-compose](https://docs.docker.com/compose/install/)

**NOTE: dependency on private repositories**

You must [create a personal github token](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in order to be able to work with private repos and export it:

```
export GITHUB_TOKEN=your token
```


```
cd benthomasson/eda
pip install -r test_requirements.txt
ansible-galaxy collection install .
pytest tests/integration
```
