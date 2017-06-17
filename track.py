
#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import time
import threading
from application.Connections import Connection
import json
import re
from bson.objectid import ObjectId
import link_parser
import subprocess

def get_info(alertDic):
    keywords = []
    alerts = []
    lang = []
    for key in alertDic:
        alert = alertDic[key]
        alerts = alerts + [alert['alertid']]
        keywords = keywords + alert['keywords']
        lang = lang + alert['lang']
    lang = list(set(lang))
    lang = [str(l) for l in lang]
    keywords = list(set(keywords))
    keywords = [str(keyword) for keyword in keywords]
    result = {
        'alerts' : sorted(alerts),
        'keywords' : keywords,
        'lang' : lang
    }
    return result

def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
            query= { '_id': "tweetDBId" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

def separates_tweet(alertDic, tweet):
    for key in alertDic:
        alert = alertDic[key]
        try:
            if tweet['lang'] in alert['lang']:
                for keyword in alert['keywords']:
                    keyword = re.compile(keyword.replace(" ", "(.?)"), re.IGNORECASE)
                    if 'extended_tweet' in tweet and 'full_text' in tweet['extended_tweet']:
                        if re.search(keyword, str(tweet['extended_tweet']['full_text'])):
                            tweet['_id'] = ObjectId()
                            Connection.Instance().db[str(alert['alertid'])].insert_one(tweet)
                            if tweet['entities']['urls'] != []:
                                link_parser.calculateLinks(alert['alertid'], tweet)
                            break
                    else:
                        if re.search(keyword, str(tweet['text'])):
                            tweet['_id'] = ObjectId()
                            Connection.Instance().db[str(alert['alertid'])].insert_one(tweet)
                            if tweet['entities']['urls'] != []:
                                link_parser.calculateLinks(alert['alertid'], tweet)
                            break
        except KeyError:
            pass

# Accessing Twitter API
consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P" # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7" # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def __init__(self,alertDic):
        self.alertDic = alertDic
        self.terminate = False
        self.connection = True
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence()
            separates_tweet(self.alertDic, tweet)
            self.connection = True
            return True
        else:
            return False

    def on_disconnect(self, notice):
        self.connection = False
        return True

    def on_error(self, status):
        print(status)
        if status == 420:
            return False

    def stop(self):
        self.terminate = True

    def on_timeout(self):
        return True # To continue listening

class StreamCreator():
    def __init__(self,alertDic):
        #This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(alertDic)

        """ TODO merge keywords langs and alerts in one method """
        self.info = get_info(alertDic= alertDic)
        self.keywords = self.info['keywords']
        self.lang = self.info['lang']
        self.alerts = self.info['alerts']
        print(self.alerts)
        print(self.keywords)
        print(self.lang)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target = self.stream.filter, kwargs = {'track':self.keywords, 'languages':self.lang} )
    def start(self):
        try:
            self.t.deamon = True
            self.t.start()
        except Exception as e:
            f = open('../log.txt', 'a+')
            f.write(e)
            f.close()
    def terminate(self):
        self.l.running = False
        self.l.stop()
        self.l.terminate = True
    def checkAlive(self):
        return self.t.isAlive()
    def checkConnection(self):
        if self.l is not None:
            return self.l.connection
        else:
            return False
