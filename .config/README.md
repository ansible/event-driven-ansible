`manifest.txt` contains the exact list of files we do expect to be inside
the built collection .tar.gz file. This is used to verify that the build
process has not missed any files or included any extra files.

If you add new files, you might need to also update this file or the CI/CD
pipeline will complain about it being out-of sync.

# Requirements

All `requirements*.in` files need this names in order to allow dependabot
to [function correctly](https://github.com/dependabot/dependabot-core/issues/10007).
