# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.
Every new feature should be tested and documented.
New source plugins or source filters will be evaluated for inclusion in the collection and might be rejected. Please consider the option of creating a new collection for your plugins if it is not a good fit for this collection.

If you are new here, read the [Quick-start development guide first](https://docs.ansible.com/ansible/devel/community/create_pr_quick_start.html).

## Code of Conduct

The ansible.eda collection follows the Ansible project's [Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html). Please read and familiarize yourself with this document.

## Submitting Issues

All software has bugs, and the amazon.aws collection is no exception. When you find a bug, you can help tremendously by telling us [about it](https://github.com/ansible/event-driven-ansible/issues/new/choose).

If you should discover that the bug you're trying to file already exists in an issue, you can help by verifying the behavior of the reported bug with a comment in that issue, or by reporting any additional information

## Writing New Code

## Cloning

Due to ansible-test own requirements, you must clone the repository into
a directory structure such `ansible_collections/ansible/eda`. This will allow
ansible-test to test your code without having to install the collection.

## Pre-commit

We recommend running pre-commit prior to submitting pull requests. A [pre-commit config](.pre-commit-config.yaml) file is included in this repository and the following steps will get you up and running with pre-commit quickly:

1. Install pre-commit:

        pip install pre-commit

2. Deploy the pre-commit config:

        pre-commit install

Pre-commit is now set up to run each time you create a new commit. If you wish to run pre-commit against all tracked files in the repository without performing a commit, you can run:

```shell
pre-commit run --all
```

# CI testing

This collection uses GitHub Actions to run Sanity, Integration and Units to validate its content.

# Adding tests

When fixing a bug, first reproduce it by adding a task as reported to a suitable file under the tests/integration/targets/<module_name>/tasks/ directory and run the integration tests as described below. The same is relevant for new features.

It is not necessary but if you want you can also add unit tests to a suitable file under the tests/units/ directory and run them as described below.

# Checking your code locally

It will make your and other people's life a bit easier if you run the tests locally and fix all failures before pushing. If you're unable to run the tests locally, please create your PR as a draft to avoid reviewers being added automatically.

## Running tests for source plugins

Running the tests requires `ansible-rulebook` to be installed. Please review the [ansible-rulebook requirements](https://ansible.readthedocs.io/projects/rulebook/en/latest/installation.html#requirements), but do not install `ansible-rulebook` manually. It will be installed via the test requirements.

We recommend setting up a Python virtual environment to install the test dependencies into:

1. Initiate the virtual environment:

        python -m venv venv
        source venv/bin/activate

2. Export the `JAVA_HOME` environment variable required by `ansible-rulebook`:

        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk

3. Install the test requirements:

        pip install -r .config/requirements.in

## Sanity and Unit tests

Sanity and unity tests can easily be run via tox:

```shell
tox -e py
```

## Integration tests

Integration tests require the addition of [docker](https://docs.docker.com/engine/install/) or [podman](https://podman.io/getting-started/installation).

Then install the collection directly from your local repo and execute the tests:

```shell
tox -e integration
```
