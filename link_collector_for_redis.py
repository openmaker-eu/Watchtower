import time

from redis import Redis
from rq import Queue

import link_parser
import pymongo

from application.Connections import Connection
from redis import StrictRedis

redisConnection = StrictRedis(host='localhost', port=6379, db=1)
redisConnection.set('unshort', 0)
redisConnection.set('search_link_db', 0)
redisConnection.set('search_link_db_update', 0)
redisConnection.set('link_parser', 0)
redisConnection.set('search_duplicate_link', 0)
redisConnection.set('search_duplicate_link_update', 0)
redisConnection.set('search_shortlink_db', 0)
redisConnection.set('search_shortlink_db_update', 0)



redis_conn = Redis()
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
                q.enqueue_call(func=link_parser.calculateLinks,
                               args=(data,Connection.Instance().machine_host,),
                               timeout=20)
    time.sleep(15)
