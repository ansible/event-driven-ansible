#!/bin/bash -eu
JOBS_PRODUCING_COVERAGE=7
declare -a FOUND_FILES
# IFS=$'\n' FOUND_FILES=( $(find . -name coverage.xml) )
while IFS='' read -r line; do FOUND_FILES+=("$line"); done < <(find . -name coverage.xml)

if [ "${#FOUND_FILES[@]}" -ne "${JOBS_PRODUCING_COVERAGE}" ]; then
    echo "::error::Broken CI/CD setup, found ${#FOUND_FILES[@]} coverage.xml file(s) instead of expected ${JOBS_PRODUCING_COVERAGE}. Found: ${FOUND_FILES[*]}"
    exit 1
fi
