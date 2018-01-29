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

consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

blacklist = ["party", "erasmus", "deal", "discount"]
numOfTweets = 10

# in month
timeThreshold = 12

local_infl_size = 40  # local influencers size
keyword_size = 10
signal_strength = 1
FOLLOWING_LIMIT = 20000


def filterAudience(p, keywords, verbose=False):
    if verbose:
        print("Filter " + p["name"] + " ?")

    if any(word in p["description"] for word in blacklist):
        return "Blacklisted word in description"
    else:
        if verbose:
            print("Fetching tweets")
        try:
            status_list = list(tweepy.Cursor(api.user_timeline, id=p[
                               "id"], tweet_mode='extended').items(numOfTweets))
        except tweepy.error.TweepError:
            if verbose:
                print("    Error fetching tweets")
                print("==============================")
            return False

        if not status_list:
            if verbose:
                print("No Tweets !")
                print("==============================")
            return "No Tweets"

        hashtags = set([str(x["text"]).lower()
                        for y in status_list for x in y.entities.get("hashtags")])
        last_nth_tweet_date = status_list[-1].created_at

        if verbose:
            print("hashtags of last " + str(numOfTweets) + " tweets")
            print(list(hashtags))
            print("date of last " + str(numOfTweets) + ". tweet")
            print(last_nth_tweet_date)

        # Time difference in seconds
        timeDiff = (datetime.now() - last_nth_tweet_date).total_seconds()

        # Time threshold
        timeThresholdInSeconds = timeThreshold * 30 * 24 * 60 * 60

        # Count  of keywords in tweets
        fullTexts = [x.full_text for x in status_list]
        count = countKeywordsInTweet(fullTexts, keywords, verbose)
        if verbose:
            print("Count of keywords = ", count)

        # If last tweets are not up-to-date or hashtags do not contain any of
        # the given keywords
        if timeDiff > timeThresholdInSeconds:
            if verbose:
                print("==============================")
            return "Tweets are outdated"
        elif (not any(keyword in hashtags for keyword in keywords)) and sum(count) == 0:
            if verbose:
                print("==============================")
            return "Hashtags and tweets unrelated"

    if verbose:
        print("==============================")
    return "Passed filters"


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


def countOccurences(fullTextTokens, query, verbose=False):
    count = 0
    if query and fullTextTokens:
        # First try each word for equality
        for word in fullTextTokens:
            if word == query:
                count += 1
                if verbose:
                    print("One Word - MATCH")
        # Word 2-gram
        for index in range(len(fullTextTokens) - 1):
            if (fullTextTokens[index] + fullTextTokens[index + 1]) == query:
                count += 1
                if verbose:
                    print("Two Words - MATCH")
    return count


def countKeywordsInTweet(fullTexts, queries, verbose=False):
    count = [0] * len(queries)
    for fullText in fullTexts:
        if verbose:
            print("full_text : " + fullText)
        fullTextTokens = tokenize(fullText)
        for index, query in enumerate(queries):
            if verbose:
                print("query " + query)
            count[index] += countOccurences(fullTextTokens, query, verbose)
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
    req = urllib2.Request(urllink)
    resp = urllib2.urlopen(req).read()
    hashtags = json.loads(resp)["hashtags"]
    keywords = [str(x["hashtag"]).lower() for x in hashtags]
    return keywords


def fetchKeywordsTest(topicID):
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


def main():
    if len(sys.argv) != 3:
        print('Usage : "python filter_audience.py topicID location"')
        return

    topicID = int(sys.argv[1])
    location = sys.argv[2]

    topics = getTopics()

    if topicID not in topics.keys():
        print("topicID does not exist. Try one of these :")
        print(topics)
        return

    keywords = fetchKeywordsTest(topicID)[:keyword_size]

    loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct(
        'id', {'predicted_location': location, '$where': 'this.influencers.length > ' + str(signal_strength)})
    audience = Connection.Instance().audienceDB['all_audience'].aggregate(
        [
            {'$match': {'id': {'$in': loc_filtered_audience_ids},
                        'friends_count': {'$lt': FOLLOWING_LIMIT}}},
            {'$project': {'_id': 0}},
            {'$sort': {'followers_count': -1}}
        ],
        allowDiskUse=True
    )
    audience = list(audience)
    local_influencers = audience[:local_infl_size]

    f = [filterAudience(x, keywords) for x in local_influencers]

    print(f)

if __name__ == "__main__":
    main()
