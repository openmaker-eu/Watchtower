import sys
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))

import tweepy  # Twitter API helper package
from tweepy import OAuthHandler

from application.Connections import Connection

import time
import datetime

from pymongo import UpdateOne

consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

number_of_tweets = 10
batch_size = 850   

def getTweets(id,number_of_tweets):
    '''
    Get last tweets of account with 'id' from twitter
    '''
    try:
        status_list = [x._json for x in tweepy.Cursor(api.user_timeline, id=id, tweet_mode='extended').items(number_of_tweets)]
    except tweepy.error.TweepError as e:
        return None

    if not status_list:
        return None

    return status_list

def saveTweetsToDB(batch):
    # For non processed ones, simply fetch tweets and write to database. For others, if last processed time
    # is older than 20 hours, then also fetch tweets and write to database otherwise do nothing.
    if batch:
        tweets = {}
        for t in batch:
            if t["processed_once"] and (datetime.datetime.utcnow() - t["last_processed"]).total_seconds() < 72000:
                continue
            t_id = t["id"]
            tweets[t_id] = getTweets(t_id, number_of_tweets)

        requests = [UpdateOne({"id": t_id},{"$set" : {"processed_once": True,"last_processed": datetime.datetime.utcnow(), "tweets": tweets_of_id}}) for t_id, tweets_of_id in tweets.items()]
        Connection.Instance().MongoDBClient.last_tweets["tweets"].bulk_write(requests, ordered=False)

def updateTweetsDB():
    cursor = Connection.Instance().MongoDBClient.last_tweets["tweets"].find({"processed_once" : False} ,{"tweets":0, "_id" : 0}).sort("processed_once" , -1).limit(batch_size)

    page_no = 1
    while cursor.count(with_limit_and_skip=True):
        print("At page {}".format(page_no))
        batch = list(cursor)
        saveTweetsToDB(batch)
        print("... Done !")
        cursor = Connection.Instance().MongoDBClient.last_tweets["tweets"].find({"processed_once" : False} ,{"tweets":0, "_id" : 0}).sort("processed_once" , -1).limit(batch_size)
        page_no += 1

if __name__ == "__main__":
    updateTweetsDB()