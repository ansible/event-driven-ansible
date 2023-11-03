#!/usr/bin/env bash
# Generate self-signed certificate for Kafka broker
# Greatly inspired by https://github.com/ansibleinc/cp-demo/blob/master/scripts/security/certs-create-per-user.sh
set -e

CA_PATH=$(dirname "${BASH_SOURCE[0]}")

# Generate CA
openssl req -new -x509 -keyout snakeoil-ca.key -out snakeoil-ca.crt -days 365 -subj '/CN=snakeoil.ansible.com/OU=TEST/O=ANSIBLE/L=Boston/ST=MA/C=US' -passin pass:ansible -passout pass:ansible

# Create broker keystore
keytool -genkey -noprompt \
    -alias broker \
    -dname "CN=broker,OU=TEST,O=ANSIBLE,L=Boston,S=MA,C=US" \
    -ext "SAN=dns:broker,dns:localhost" \
    -keystore kafka.broker.keystore.jks \
    -keyalg RSA \
    -storepass ansible \
    -keypass ansible \
    -storetype pkcs12

# Create broker CSR
keytool -keystore kafka.broker.keystore.jks -alias broker -certreq -file broker.csr -storepass ansible -keypass ansible -ext "SAN=dns:broker,dns:localhost"

# Sign the host certificate with the certificate authority (CA)
# Set a random serial number (avoid problems from using '-CAcreateserial' when parallelizing certificate generation)
CERT_SERIAL=$(awk -v seed="$RANDOM" 'BEGIN { srand(seed); printf("0x%.4x%.4x%.4x%.4x\n", rand()*65535 + 1, rand()*65535 + 1, rand()*65535 + 1, rand()*65535 + 1) }')
openssl x509 -req -CA "${CA_PATH}/snakeoil-ca.crt" -CAkey "${CA_PATH}/snakeoil-ca.key" -in broker.csr -out broker-ca-signed.crt -sha256 -days 365 -set_serial "${CERT_SERIAL}" -passin pass:ansible -extensions v3_req -extfile <(cat <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
CN = broker
[v3_req]
extendedKeyUsage = serverAuth, clientAuth
EOF
)

# Sign and import the CA cert into the keystore
keytool -noprompt -keystore kafka.broker.keystore.jks -alias snakeoil-caroot -import -file "${CA_PATH}/snakeoil-ca.crt" -storepass ansible -keypass ansible

# Sign and import the host certificate into the keystore
keytool -noprompt -keystore kafka.broker.keystore.jks -alias broker -import -file broker-ca-signed.crt -storepass ansible -keypass ansible -ext "SAN=dns:broker,dns:localhost"

# Create truststore and import the CA cert
keytool -noprompt -keystore kafka.broker.truststore.jks -alias snakeoil-caroot -import -file "${CA_PATH}/snakeoil-ca.crt" -storepass ansible -keypass ansible
