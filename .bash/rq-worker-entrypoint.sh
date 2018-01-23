#!/bin/bash

pushd /root/cloud

dir="$(pipenv --venv)/bin/activate"

source $dir

for VARIABLE in 1 .. ${WORKER_NUMBER}
do
    python3 /root/cloud/collector_module/worker.py &
done

python3 /root/cloud/collector_module/worker.py