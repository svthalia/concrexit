#!/bin/bash

exists()
{
  command -v "$1" >/dev/null 2>&1
}

yesno () {
    if exists whiptail; then
        whiptail --yesno "$1" 10 60
        return
    elif exists dialog; then
        dialog --yesno "$1" 10 60
        return
    fi

    read -p "$1 (y/N)" answer
    case ${answer:0:1} in
        y|Y )
            return 0
        ;;
        * )
            return 1
        ;;
    esac
}

set -e

if [ "$1" = "" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi
version="$1"
version_sane="$(echo $version | sed 's/^[0-9]\.[0-9]\+\.[0-9]\+$/YES/')"
if [ "$version_sane" != "YES" ]; then
    echo "Version should be in the format '1.23.45'"
    exit 1
fi
version_major=${version%.*}

echo "Changing directory to root of repository"
cd "${0%/*}"

echo "Changing to branch 'release/$version_major'"
git checkout "release/$version_major"

tag="$(git tag --contains)"
branch="$(git symbolic-ref --quiet --short HEAD || git rev-parse --short HEAD)"
if [ "$tag" = "v$version" ]; then
    echo "Already tagged!"
else
    echo "Creating new tag 'v$version"
    git tag --annotate "v$version"
fi

if ! yesno "Do you want to build a docker container?"; then
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "Unclean working directory!"
    git status
    exit 1
fi

docker_tag="registry.gitlab.com/thaliawww/concrexit:$version"

docker build -t "$docker_tag" .

if yesno "Do you want to push the container?"; then
    docker push "$docker_tag"
fi
