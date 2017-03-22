#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import time
import threading
from application.Connections import Connection
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def get_keywords(alertDic):
    keywords = set()
    for key,alert in alertDic:
        keywords.union(alert['keywords'])
    return keywords

def get_lang(alertDic):
    lang = set()
    for key,alert in alertDic:
        lang.union(alert['lang'])
    return lang

def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
            query= { '_id': "tweetDBId" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

def separates_tweet(alertDic, tweet):
    for alert in alertDic:
        for keyword in alert['keyword']:
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            if re.search(keyword, tweet):
                Connection.Instance().db[str(alert['alertid'])].insert_one(tweet)

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
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence()
            separates_tweet(alertDic, tweet)
            Connection.Instance().db["all"].insert_one(tweet)
            return True
        else:
            return False

    def on_error(self, status):
        if self.terminate == True:
            return False

    def stop(self):
        self.terminate = True

class StreamCreator():
    def __init__(self,alertDic):
        #This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(alertDic)
        self.keywords = get_keywords(alertDic= alertDic)
        self.lang = get_lang(alertDic= alertDic)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target = self.stream.filter, kwargs = {'track':keywords, 'languages':lang} )
    def start(self):
        self.t.deamon = True
        self.t.start()
    def terminate(self):
        self.l.running = False
        self.l.stop()
        self.l.terminate = True
    def checkAlive(self):
        return self.t.isAlive()
