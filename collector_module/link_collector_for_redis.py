import sys
import time

sys.path.append('./')

from redis import Redis, ConnectionPool
from rq import Queue

from application.utils import link_parser
from application.Connections import Connection

from decouple import config

pool = ConnectionPool(host='db', port=6379, password=config("REDIS_PASSWORD"), db=0)
redis_conn = Redis(connection_pool=pool)
q = Queue(connection=redis_conn)  # no args implies the default queue

while True:
    for collection in sorted(list(Connection.Instance().db.collection_names()), reverse=True):
        if str(collection) != 'counters':
            print('id: ', collection)
            tweets = list(Connection.Instance().db[str(collection)].find({'redis': {'$exists': True}, 'redis': False}, \
                                                                         {'id_str': 1, '_id': 0, 'timestamp_ms': 1,
                                                                          'user': 1, 'entities.urls': 1}))
            print(len(tweets))
            for tweet in tweets:
                Connection.Instance().db[str(collection)].find_one_and_update(
                    {'id_str': tweet['id_str'], 'redis': {'$exists': True}, 'redis': False}, {'$set': {'redis': True}})
                data = {
                    'alertid': collection,
                    'tweet': tweet,
                    'channel': 'twitter'
                }
                q.enqueue_call(func=link_parser.calculate_links,
                               args=(data, config("HOST_IP"),),
                               at_front=True,
                               timeout=20)
    time.sleep(15)
