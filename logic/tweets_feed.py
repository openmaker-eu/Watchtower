__author__ = ['Enis Simsar']

import pymongo
from application.Connections import Connection


def get_tweets(topic_id):
    tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                               'created_at': 1, "_id": 0}).sort(
        [('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


def get_skip_tweets(topic_id, last_tweet_id):
    tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$lt': int(last_tweet_id)}},
                                                          {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                           'created_at': 1, "_id": 0}) \
        .sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


def check_tweets(topic_id, newest_id):
    if int(newest_id) == -1:
        tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                   'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$gt': int(newest_id)}},
                                                              {'tweetDBId': 1, "text": 1, "user": 1, 'created_at': 1,
                                                               "_id": 0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)


def get_new_tweets(topic_id, newest_id):
    if int(newest_id) == -1:
        tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                   'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$gt': int(newest_id)}},
                                                              {'tweetDBId': 1, 'id': 1, "text": 1, "user": 1,
                                                               'created_at': 1, "_id": 0}) \
            .sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return tweets
