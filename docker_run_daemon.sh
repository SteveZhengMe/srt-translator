#!/bin/bash

# check if there are two arguments
if [ $# -ne 1 ]
then
    echo "Usage: ./docker_run.sh [local|remote]"
    exit 1
else
    # if arg is "remote", use remote image
    if [ "$1" == "remote" ]
    then
        image="stevezhengcn/srt-translator-daemon"
    else
        image="srt-translator-daemon"
    fi
fi

echo "Using image: $image"

# check if deepl_key and openai_key are set
if [ -z "$deepl_key" ] || [ -z "$openai_key" ]
then
    docker run --rm -it -v ./data/movie:/movie -v ./data/tv:/tv --env-file ./.env $image
else
    docker run --rm -it -v ./data/movie:/movie -v ./data/tv:/tv --env-file ./.env -e deepl_key -e openai_key $image
fi