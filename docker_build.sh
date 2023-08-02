#!/bin/bash

# check if there is an arg "version"
if [ -z "$1" ]
then
    echo "No version argument supplied. Using latest."
    docker build --tag srt-translator:latest .
else
    docker build --tag srt-translator:$1 --tag srt-translator:latest .
fi
