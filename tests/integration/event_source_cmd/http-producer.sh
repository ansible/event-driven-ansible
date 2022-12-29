#!/bin/bash -eux

URL=$1

for n in {1..3}; do
    curl "$URL" -d "{\"status\": \"Running\", \"number\": $n}"
    sleep 1
done


