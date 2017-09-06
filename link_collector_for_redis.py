import time

from redis import Redis
from rq import Queue

import link_parser
from application.Connections import Connection

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
                               args=(data,),
                               timeout=20)
    time.sleep(15)
