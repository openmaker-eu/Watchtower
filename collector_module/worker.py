import os
import sys

from redis import from_url
from rq import Worker, Queue, Connection
from decouple import config

sys.path.insert(0,config("ROOT_DIR"))

listen = ['default']

redis_url = 'redis://:{0}@db:6379'.format(config("REDIS_PASSWORD"))

conn = from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()