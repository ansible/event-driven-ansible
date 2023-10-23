#!/usr/bin/env bash
set -e
DIR=$(dirname "${BASH_SOURCE[0]}")
rm -f "${DIR}/snakeoil-ca.key" \
      "${DIR}/snakeoil-ca.crt" \
      "${DIR}/broker.csr" \
      "${DIR}/broker-ca-signed.crt" \
      "${DIR}/kafka.broker.keystore.jks" \
      "${DIR}/kafka.broker.truststore.jks"
