#!/bin/bash

# check if deepl_key and openai_key are set
if [ -z "$deepl_key" ] || [ -z "$openai_key" ]
then
    docker run --rm -it -v ./data:/app/data --env-file ./.env stevezhengcn/srt-translator
else
    docker run --rm -it -v ./data:/app/data --env-file ./.env -e deepl_key -e openai_key stevezhengcn/srt-translator
fi