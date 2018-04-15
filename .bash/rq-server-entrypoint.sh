#!/bin/bash

password="$(echo ${REDIS_PASSWORD} | sha1sum)"
echo $password

/usr/bin/redis-server --requirepass $password