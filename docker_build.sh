#!/bin/bash

# ask if user wants to push to docker hub
read -p "Do you want to push to docker hub? (y/n) " -n 1 -r REPLY

version=$(grep "version" pyproject.toml | cut -d'=' -f2)
# trim version and remove first " from version
version="${version//[[:space:]]/}"
version="${version#\"}"
version="${version%\"}"

echo "Building version $version"
docker build --tag srt-translator:$version --tag srt-translator:latest .

# push to docker hub if user wants to
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # login to docker hub
    if ! docker info > /dev/null 2>&1; then
        echo "Please login to Docker Hub (run docker login)"
        exit 1
    fi
    #echo "$docker_hub_password" | docker login -u "$docker_hub_username" --password-stdin
    docker_hub_username="stevezhengcn"
    # add latest tag and version tag
    docker tag srt-translator:latest "$docker_hub_username"/srt-translator:$version
    docker tag srt-translator:latest "$docker_hub_username"/srt-translator:latest

    # push to docker hub
    docker push "$docker_hub_username"/srt-translator:$version
    docker push "$docker_hub_username"/srt-translator:latest
fi
