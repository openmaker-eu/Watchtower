import os
import sys

import redis
from rq import Worker, Queue, Connection

sys.path.insert(0,'/root/cloud')

listen = ['default']

redis_url = 'redis://db:6379'

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()