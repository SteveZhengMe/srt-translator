#!/bin/bash

# login to docker hub
echo "$docker_hub_password" | docker login -u "$docker_hub_username" --password-stdin

# add tag
docker tag srt-translator:latest "$docker_hub_username"/srt-translator:latest

# push to docker hub
docker push "$docker_hub_username"/srt-translator:latest