#!/bin/bash -eux

if [[ $1 == "good" ]]; then
    
    for n in {1..3}; do
        echo "{\"status\": \"Running\", \"number\": $n}"
        sleep 1
    done
    
fi


if [[ $1 == "bad" ]]; then
    echo "BAD"
    sleep 1
fi

if [[ $1 == "raw" ]]; then
    echo -n "Some raw text"
    sleep 1
fi