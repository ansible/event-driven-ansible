# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.
Every new feature should be tested and documented.
New source plugins or source filters will be evaluated for inclusion in the collection and might be rejected. Please consider the option of creating a new collection for your plugins if it is not a good fit for this collection.

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

## Running tests for source plugins

Running the tests requires `ansible-rulebook` to be installed. Please review the [ansible-rulebook requirements](https://ansible-rulebook.readthedocs.io/en/stable/installation.html#requirements), but do not install `ansible-rulebook` manually. It will be installed via the test requirements.

We recommend setting up a Python virtual environment to install the test dependencies into:

1. Initiate the virtual environment:

        python -m venv venv
        source venv/bin/activate

2. Export the `JAVA_HOME` environment variable required by `ansible-rulebook`:

        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk

3. Install the test requirements:

        pip install -r test_requirements.txt

### Sanity and Unit tests

Sanity and unity tests can easily be run via tox:

```shell
tox -e py
```

### Integration tests

Integration tests require the addition of [docker](https://docs.docker.com/engine/install/) or [podman](https://podman.io/getting-started/installation) and [docker-compose](https://docs.docker.com/compose/install/).


Then install the collection directly from your local repo and execute the tests:

```shell
tox -e integration
```
