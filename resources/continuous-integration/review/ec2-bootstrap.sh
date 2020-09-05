#!/usr/bin/env bash

apt-get update
apt-get install --assume-yes \
    nginx
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common


curl --fail --silent --show-error --location https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

apt-get update
apt-get --assume-yes install docker-ce docker-ce-cli containerd.io

curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

DNS_NAME=$(curl --silent http://169.254.169.254/latest/meta-data/public-hostname)

mkdir certs
openssl req -x509 -nodes -newkey rsa:2048 -keyout "certs/${DNS_NAME}.key" -out "certs/${DNS_NAME}.crt" -subj "/C=NL/ST=Gelderland/L=Nijmegen/O=Thalia/OU=Technicie/CN=${DNS_NAME}"

cat > docker-compose.yaml <<EOF
---

version: '3.5'

services:
    nginx-proxy:
        image: jwilder/nginx-proxy
        ports:
            - 80:80
            - 443:443
        environment:
            DHPARAM_GENERATION: "false"
            DHPARAM_BITS: 2048
        volumes:
            - /var/run/docker.sock:/tmp/docker.sock:ro
            - ./certs/:/etc/nginx/certs/

    web:
        image: docker.pkg.github.com/svthalia/concrexit/commit:@version@
        entrypoint: /bin/bash
        depends_on:
            - nginx-proxy
        ports:
            - 127.0.0.1:8000:8000
        command: >-
          -c "python manage.py migrate
          && python manage.py createreviewuser --username @username@ --password @password@
          && python manage.py createfixtures -a
          && python manage.py runserver 0.0.0.0:8000"
        environment:
            VIRTUAL_HOST: "${DNS_NAME}"
EOF

docker-compose up --detach

echo "shutdown now" | at now +1 days
