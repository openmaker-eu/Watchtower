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
window_size = 850   

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

def saveTweetsToDB(batch, isProcessed):
    # For non processed ones, simply fetch tweets and write to database. For others, if last processed time
    # is older than 20 hours, then also fetch tweets and write to database otherwise do nothing.
    if batch:
        tweets = {}
        for t in batch:
            if isProcessed and (datetime.datetime.utcnow() - t["last_processed"]).total_seconds() < 72000:
                continue
            t_id = t["id"]
            tweets[t_id] = getTweets(t_id, number_of_tweets)

        requests = [UpdateOne({"id": t_id},{"$set" : {"processed_once": True,"last_processed": datetime.datetime.utcnow(), "tweets": tweets_of_id}}) for t_id, tweets_of_id in tweets.items()]
        Connection.Instance().MongoDBClient.last_tweets["tweets"].bulk_write(requests, ordered=False)

def updateTweetsDB():
    # Process users in windows of size 60
    not_processed = list(Connection.Instance().MongoDBClient.last_tweets["tweets"].find({"processed_once" : False} ,{"id":1 , "_id" : 0}))
    processed_once = list(Connection.Instance().MongoDBClient.last_tweets["tweets"].find({"processed_once" : True} , {"id":1, "last_processed" : 1, "_id" : 0}))
    ## USE SKIP LIMIT !!!
    for users, isProcessed in zip([not_processed, processed_once] , [False, True]):
        if users:
            print(("Processing non-processed ones" if not isProcessed else "Processing processed ones"))
            page = 1
            while page*window_size < len(users):
                print("...Processing page",page)
                batch = users[(page - 1)*window_size:page*window_size]
                saveTweetsToDB(batch, isProcessed)
                page += 1

            # remaining ones
            print("...Last page ...")
            batch = users[(page - 1)*window_size :]
            saveTweetsToDB(batch, isProcessed)

if __name__ == "__main__":
    updateTweetsDB()