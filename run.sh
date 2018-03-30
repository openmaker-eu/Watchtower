#!/bin/sh

eval $(cat .env | sed 's/^/export /')

echo "$(whoami)"

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

docker-compose down
docker-compose up -d
