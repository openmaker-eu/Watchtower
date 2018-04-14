#!/bin/bash

set -e

cron_name="$1"
shift
cmd="$@"

echo "cron name: " $cron_name
echo "cmd: " $cmd

cron_id=`pipenv run python3 /root/cloud/crontab_module/cron_log.py "$cron_name" 2>&1 | tail -1`

$cmd

pipenv run python3 /root/cloud/crontab_module/cron_log.py "$cron_name" $cron_id $? 2>&1