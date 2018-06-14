#!/bin/bash

set -e

# Wait for Redis server to start
sleep 10

# Could do the following if redis-tools installed:
# X="`redis-cli -h \"$CELERY_BROKER_HOST\" ping`"
# echo ${X}
#
# while  [ "${X}" != "PONG" ]; do
#     >&2 echo "Redis is unavailable: Sleeping"
#     echo "${X}"
#     sleep 5
# done
# >&2 echo "Redis is up"

cd /usr/src/app/website/
>&2 echo "Starting celery worker"
celery worker -A thaliawebsite
