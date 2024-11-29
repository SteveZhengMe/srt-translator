#!/bin/bash

# ask if user wants to push to docker hub
read -p "Build srt-translator (CLI & Daemon). Do you want to push to docker hub? (y/n) " -n 1 -r REPLY

version=$(grep "version" pyproject.toml | cut -d'=' -f2)
# trim version and remove first " from version
version="${version//[[:space:]]/}"
version="${version#\"}"
version="${version%\"}"

echo ""
echo "Version: $version"
# build cli version
docker build -f dockerfile --tag srt-translator:$version --tag srt-translator:latest .
# build daemon version
docker build -f dockerfile-daemon --tag srt-translator-daemon:$version --tag srt-translator-daemon:latest .

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
    # add latest tag and version tag to cli version
    docker tag srt-translator:latest "$docker_hub_username"/srt-translator:$version
    docker tag srt-translator:latest "$docker_hub_username"/srt-translator:latest
    # add latest tag and version tag to daemon version
    docker tag srt-translator-daemon:latest "$docker_hub_username"/srt-translator-daemon:$version
    docker tag srt-translator-daemon:latest "$docker_hub_username"/srt-translator-daemon:latest

    # push cli version to docker hub
    docker push "$docker_hub_username"/srt-translator:$version
    docker push "$docker_hub_username"/srt-translator:latest
    # push daemon version to docker hub
    docker push "$docker_hub_username"/srt-translator-daemon:$version
    docker push "$docker_hub_username"/srt-translator-daemon:latest
fi
