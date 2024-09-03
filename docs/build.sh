#!/usr/bin/env bash
set -eu

pushd "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
trap "{ popd; }" EXIT

# Determine the collection version, if current commit is tagged, use it. Otherwise, generate pre-release version.
COLLECTION_VERSION_WITH_PREFIX=$(git describe --dirty --tags --long --match "v*.*" | cut -f1,2 -d'-')
COLLECTION_VERSION=${COLLECTION_VERSION_WITH_PREFIX/v/}
echo "INFO:  Determined collection version to be ${COLLECTION_VERSION}"

# Create collection documentation
mkdir -p rst
chmod og-w rst  # antsibull-docs wants that directory only readable by itself
antsibull-docs \
    --config-file antsibull-docs.cfg \
    collection \
    --cleanup everything \
    --fail-on-error \
    --use-current \
    --squash-hierarchy \
    --dest-dir rst \
    ansible.eda

# To be included inside the built collection archive
pushd ..
mk -v changelog
cp CHANGELOG.md ./docs/rst/changelog.md
popd

cat >rst/_.rst <<EOF
:orphan:

.. toctree::
   changelog.md
EOF

# Build Sphinx site
sphinx-build -M html rst build -c . -W --keep-going

if [[ ! -f ./build/html/changelog.html ]]; then
  echo "ERROR: Changelog file not found."
fi
echo "INFO:  Finished building docs for version ${COLLECTION_VERSION} - Open it at ./docs/build/html/index.html"
