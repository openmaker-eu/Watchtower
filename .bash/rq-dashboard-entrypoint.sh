#!/bin/sh
echo ${REDIS_PASSWORD}

/usr/bin/rq-dashboard --redis-password=${REDIS_PASSWORD}  -H db
#
# if use basic auth
# /usr/bin/rq-dashboard --username <USERNAME> --password <PASSWORD> -H ${DB_PORT_6379_TCP_ADDR}
#
