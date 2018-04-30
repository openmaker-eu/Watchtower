#!/bin/bash

set -e

cron_name="$1"
cron_frequency="$2"
shift
shift
cmd="$@"

echo "cron name: " $cron_name
echo "cmd: " $cmd

cron_id=`pipenv run python3 /root/cloud/crontab_module/cron_log.py "$cron_name" "$cron_frequency" 2>&1 | tail -1`

echo "$cron_name" >> /var/log/cron_daily.log

status=0

if ! cron_log=`$cmd 2>&1`; then
    status=1
fi

echo $cron_log >> /var/log/cron_daily.log

pipenv run python3 /root/cloud/crontab_module/cron_log.py "$cron_name" $cron_id $status