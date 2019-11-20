#!/bin/sh

# From https://docs.docker.com/install/linux/docker-ce/ubuntu/
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io

docker volume create concrexit_data
docker run --name concrexit_migrate \
  --rm \
  --mount source=concrexit_data,target=/usr/src/app/website/ \
  thalia/concrexit:@version@ migrate

docker run --name concrexit_superuser \
  --rm \
  --mount source=concrexit_data,target=/usr/src/app/website/ \
  thalia/concrexit:@version@ createreviewuser \
  --username @username@ --password @password@

docker run --name concrexit_fixtures \
  --rm \
  --mount source=concrexit_data,target=/usr/src/app/website/ \
  thalia/concrexit:@version@ createfixtures -a

docker run --name concrexit_web \
  --detach \
  --publish 0.0.0.0:80:80 \
  --mount source=concrexit_data,target=/usr/src/app/website/ \
  thalia/concrexit:@version@ runserver 0.0.0.0:80

echo "shutdown now" | at now +2 days
