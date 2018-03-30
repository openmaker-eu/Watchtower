#!/bin/sh

service cron start
pipenv shell python3 ./crontab_module/crontab_module.py
