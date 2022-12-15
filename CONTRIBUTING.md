## Contributing
Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

### Pre-commit
We recommend running pre-commit prior to submitting pull requests. A [pre-commit config](.pre-commit-config.yaml) file is included in this repository and the following steps will get you up and running with pre-commit quickly:

1. Install pre-commit:

        pip install pre-commit

2. Deploy the pre-commit config:

        pre-commit install

Pre-commit is now set up to run each time you create a new commit. If you wish to run pre-commit against all tracked files in the repository without performing a commit, you can run:

```
pre-commit run --all
```
