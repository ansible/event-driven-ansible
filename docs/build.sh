#!/usr/bin/env bash
set -eu

pushd "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
trap "{ popd; }" EXIT

GALAXY_VERSION=$(python -c "import yaml; print(yaml.safe_load(open('../galaxy.yml'))['version'])")
# Determine the collection version, if current commit is tagged, use it. Otherwise, generate pre-release version.

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

CHANGELOG_VERSION=$(grep -m 1 '^#' rst/changelog.md  | awk '/^#/ {print $2; exit}' | sed 's/v//')

if [[ "${GALAXY_VERSION}" != "${CHANGELOG_VERSION}" ]]; then
  echo "WARN: galaxy.yaml collection version ${GALAXY_VERSION} does not match the changelog version ${CHANGELOG_VERSION}. Please update the galaxy.yaml version to match the changelog version."
fi

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
echo "INFO:  Finished building docs for version ${GALAXY_VERSION} - Open it at ./docs/build/html/index.html"

cd ..
# Determine if current commit is tagged and if it matches the collection version,
# if not, it will generate a pre-release version when building the collection.
GIT_TAG_VERSION=$(git describe --tags | sed 's/v//')
if [[ "${GALAXY_VERSION}" != "${GIT_TAG_VERSION}" ]]; then
    GALAXY_VERSION=${GALAXY_VERSION}-dev
    echo "WARNING:  Current commit is not tagged, using a temporary pre-release version ${GALAXY_VERSION} instead during build."
    sed -i.bak -e "s/^version:.*/version: ${GALAXY_VERSION}/" galaxy.yml
    rm galaxy.yml.bak
fi

echo "INFO:  Building collection version ${GALAXY_VERSION}..."

echo "INFO:  Cleaning up old files"
rm -f ./*.tar.gz importer_result.json

echo "INFO:  Run galaxy-importer, which calls 'ansible-galaxy collection build .' itself"
# produces importer_result.json
GALAXY_IMPORTER_CONFIG=.config/galaxy-importer.cfg python3 -m galaxy_importer.main --git-clone-path=. --output-path=.

echo "INFO:  Check if importer_result.json is not empty"
ARCHIVE=$(python3 -c "import json; print(json.load(open('importer_result.json'))[-1])")

echo "INFO:  Check that list of files (manifest) inside the collection archive is the expected one."
tar -tf "$ARCHIVE" | LC_ALL=C sort -f > .config/manifest.txt
sync

echo "INFO:  Restore temporary modified galaxy.yml file."
git checkout HEAD -- galaxy.yml >/dev/null

git --no-pager diff -U0 --minimal || {
    echo "ERROR: Manifest at .config/manifest.txt changed, please update it."
    exit 3
}
echo "INFO:  Galaxy importer check passed."

echo "INFO:  Determined collection version ${GALAXY_VERSION}"
