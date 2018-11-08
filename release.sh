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
version_sane="$(echo $version | sed -Ee 's/^[0-9]{1,}\.[0-9]{1,}$/YES/')"
if [ "$version_sane" != "YES" ]; then
    echo "Version should be in the format '12.34'"
    exit 1
fi
version_major=${version%.*}

echo "Changing directory to root of repository"
cd "${0%/*}"

echo "Making sure we're up-to-date"
git fetch --tags

echo "Changing to branch 'release/$version_major'"
git checkout "release/$version_major"

tag="$(git tag --contains)"
branch="$(git symbolic-ref --quiet --short HEAD || git rev-parse --short HEAD)"
if [ "$tag" = "v$version" ]; then
    echo "Already tagged!"
else
    echo "Creating new tag 'v$version'"
    git tag --annotate "v$version"
fi

if yesno "Do you want to push the tag to the repository?"; then
    echo "Pushing tags:"
    git push --tags
    echo "Don't forget to fill in the release description on the website:"
    echo "https://gitlab.science.ru.nl/thalia/concrexit/tags/v$version/release/edit"
fi
