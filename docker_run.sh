#!/bin/bash

# check if there are two arguments
if [ $# -ne 2 ]
then
    echo "Usage: ./docker_run.sh [local|remote] [command]"
    exit 1
else
    # if arg is "remote", use remote image
    if [ "$1" == "remote" ]
    then
        image="stevezhengcn/srt-translator"
    else
        image="srt-translator"
    fi
fi

echo "Using image: $image"

# check if deepl_key and openai_key are set
if [ -z "$deepl_key" ] || [ -z "$openai_key" ]
then
    docker run --rm -it -v ./data/subs:/app/data -v ./data:/app/export --env-file ./.env $image $2
else
    docker run --rm -it -v ./data/subs:/app/data -v ./data:/app/export --env-file ./.env -e deepl_key -e openai_key $image $2
fi