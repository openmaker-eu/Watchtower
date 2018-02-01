# -*- coding: utf-8 -*-
import sys  # to get system arguments
import time  # for debug
import re  # for regex in location filtering
import pymongo  # for pymongo functions
import numpy as np  # for sampling
# to print the date & time in the output log whenever this script is run
# OR for time related checks
from datetime import datetime
from pdb import set_trace
import tweepy  # Twitter API helper package
from tweepy import OAuthHandler
from tweepy.error import TweepError
from application.Connections import Connection
import urllib
import json
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import *
from decouple import config
import argparse


consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

blacklist = ["party", "erasmus", "deal", "discount"]
numOfTweets = 10

timeThreshold = 12  # in month
local_infl_size = 40  # local influencers size
keyword_size = 10

default_signal_strength = 4  
default_following_limit = 20000

def filterAudience(p, keywords):
    verboseprint("Filter " + p["name"] + " ?", debugLevel=1)

    if any(word in p["description"] for word in blacklist):
        verboseprint("RESULT = FILTERED", debugLevel=1)
        verboseprint("==============================", debugLevel=1)
        return False
    else:
        verboseprint("Fetching tweets", debugLevel=1)
        try:
            status_list = list(tweepy.Cursor(api.user_timeline, id=p[
                               "id"], tweet_mode='extended').items(numOfTweets))
        except tweepy.error.TweepError:
            verboseprint(
                "Error fetching tweets\n==============================", debugLevel=1)
            return False

        if not status_list:
            verboseprint(
                "No Tweets !\n==============================", debugLevel=1)
            return False

        hashtags = set([str(x["text"]).lower()
                        for y in status_list for x in y.entities.get("hashtags")])
        last_nth_tweet_date = status_list[-1].created_at

        verboseprint("hashtags of last " + str(numOfTweets) +
                     " tweets", debugLevel=0)
        verboseprint(list(hashtags), debugLevel=0)
        verboseprint("date of last " + str(numOfTweets) +
                     ". tweet", debugLevel=0)
        verboseprint(last_nth_tweet_date, debugLevel=0)

        # Time difference in seconds
        timeDiff = (datetime.now() - last_nth_tweet_date).total_seconds()

        # Time threshold
        timeThresholdInSeconds = timeThreshold * 30 * 24 * 60 * 60

        # Count  of keywords in tweets
        fullTexts = [x.full_text for x in status_list]
        count = countKeywordsInTweet(fullTexts, keywords)
        verboseprint("Count of keywords = ", count, debugLevel=0)

        # If last tweets are not up-to-date or hashtags do not contain any of
        # the given keywords
        tweets_outdated = (timeDiff > timeThresholdInSeconds)
        hashtags_unrelated = (
            not any(keyword in hashtags for keyword in keywords)) and sum(count) == 0

        if tweets_outdated or hashtags_unrelated:
            verboseprint("RESULT = FILTERED", debugLevel=1)
            verboseprint("==============================", debugLevel=1)
            return False

    verboseprint("RESULT = PASSED", debugLevel=1)
    verboseprint("==============================", debugLevel=1)
    return True


def tokenize(text):
    stop_words = set(stopwords.words('english'))
    delimiters = ["<", ">", "#", "@", "“", "”", '.', "‘", '—', '"', ',',
                  "’", "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '&',  "-"]
    extraStopWords = ['a', 'in', "--", "---", "the", "bi", "https"]
    stop_words.update(delimiters)
    stop_words.update(extraStopWords)
    tokens = nltk.word_tokenize(text)
    tokens = [i.lower().translate({ord(c): None for c in delimiters})
              for i in tokens if i.lower() not in stop_words]
    return tokens


def countOccurences(fullTextTokens, query):
    count = 0
    if query and fullTextTokens:
        # First try each word for equality
        for word in fullTextTokens:
            if word == query:
                count += 1
        # Word 2-gram
        for index in range(len(fullTextTokens) - 1):
            if (fullTextTokens[index] + fullTextTokens[index + 1]) == query:
                count += 1
    return count


def countKeywordsInTweet(fullTexts, queries):
    count = [0] * len(queries)
    for fullText in fullTexts:
        fullTextTokens = tokenize(fullText)
        for index, query in enumerate(queries):
            count[index] += countOccurences(fullTextTokens, query)
    return count


def getTopics():
    '''
        Returns all topics in the OpenMaker staging database.
    '''
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
        )
        cur.execute(sql)
        topics = dict()
        for topic_id, topic_name in cur.fetchall():
            topics[int(topic_id)] = topic_name
        return topics


def fetchKeywords(topicID):
    urllink = "http://" + \
        config("HOST_IP") + ":8484/api/v1.3/get_hashtags?topic_id=" + str(topicID)
    with urllib.request.urlopen(urllink) as response:
        html = response.read()
    hashtags = json.loads(html)["hashtags"]
    keywords = [str(x["hashtag"]).lower() for x in hashtags]
    return keywords


def fetchAllKeywords():
    topics = getTopics()
    keyword_per_topic = {}
    for topic in topics:
        keywords = fetchKeywords(topic)
        keyword_per_topic[topic] = keywords
    return keyword_per_topic


def getInfluencerParameters():
    '''
    Fetch influencer parameters from database and return a dict
    with (topicID,location) pairs as keys.
    '''
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, location, signal_strength, following_limit "
            "FROM influencer_parameters "
        )
        cur.execute(sql)
        d = {(x[:2]): x[2:] for x in cur.fetchall()}
        return d


def findLocalInfluencers(location, topicID, keywords):
    signal_strength, following_limit = parameters[topicID, location] if (
        topicID, location) in parameters else [default_signal_strength, default_following_limit]

    verboseprint("Fetching audience profiles from database", debugLevel=2)
    loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct(
        'id', {'predicted_location': location, '$where': 'this.influencers.length > ' + str(signal_strength)})
    audience = Connection.Instance().audienceDB['all_audience'].aggregate(
        [
            {'$match': {'id': {'$in': loc_filtered_audience_ids},
                        'friends_count': {'$lt': following_limit}}},
            {'$project': {'_id': 0}},
            {'$sort': {'followers_count': -1}}
        ],
        allowDiskUse=True
    )
    audience = list(audience)
    local_influencers = audience[:local_infl_size]

    passed = [x for x in local_influencers if filterAudience(x, keywords)]

    return passed


def verboseprint(*a, **k):
    if "debugLevel" in k and k["debugLevel"] >= args.verbose:
        del k["debugLevel"]
        print(*a, **k)


def writeLocalInfluencersToDB(location, topicID, keywords):
    passed = findLocalInfluencers(location, topicID, keywords)

    if len(passed) == 0:
        verboseprint(
            "No local influencers could be found. Collection is not added to DB !", debugLevel = 2)
        return

    # save the sample audience to MongoDB
    Connection.Instance().local_influencers_DB[
        str(topicID) + "_" + str(location)].drop()
    try:
        Connection.Instance().local_influencers_DB[str(
            topicID) + "_" + str(location)].insert_many(passed)
    except Exception as e:
        verboseprint("Exception in insert_many:" + str(e), debugLevel=2)


def writeAllLocalInfluencersToDB():
    locations = ["es", "gb", "sk", "it", "tr"]
    for topicID in topics:
        keywords = fetchKeywords(topicID)[:keyword_size]
        for location in locations:
            verboseprint(
                "Now Processing => topicID = {}, location = {}".format(topicID, location), debugLevel=2)
            writeLocalInfluencersToDB(location, topicID, keywords)
            verboseprint("###DONE###", debugLevel = 2)


parser = argparse.ArgumentParser(description='This.')
parser.add_argument("-v", "--verbose", type=int, default=2,
                    nargs="?", const=2, choices=set((0, 1, 2)))
args = parser.parse_args()

topics = getTopics()
parameters = getInfluencerParameters()

if __name__ == "__main__":
    writeAllLocalInfluencersToDB()
