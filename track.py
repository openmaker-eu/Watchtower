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


def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
            query= { '_id': "tweetDBId" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

#Variables that contains the user credentials to access Twitter API
access_token = "455237513-3NZrkuCQMOldFRhuC53r8WoKDY7T5MxjqYyWgzHb"
access_token_secret = "YnCFJANRcEnPPqUM8TcbVbHS0lQX3KjQnKdPU3XdG2sTy"
consumer_key = "K6Rk0fGEFB6gtKYuzaBnTMT9T"
consumer_secret = "F3NryI1Nw3fXGawq2DYQBeowmzsmxWba4wLgPKyUucudwJ35mY"

consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P" # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7" # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_token_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def __init__(self,alert):
        self.terminate = False
        self.campaignId = alert['id']
        self.campaignName = alert['name']
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            #print data
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence()
            Connection.Instance().db[str(self.campaignId)].insert_one(tweet) #this creates tweets collection, if there is one then write on it
            return True
        else:
            return False

    def on_error(self, status):
        print status
        if self.terminate == True:
            return False

    def stop(self):
        self.terminate = True


class StreamCreator():
    def __init__(self,alert):
        #This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(alert)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target = self.stream.filter, kwargs = {'track':alert['keywords'],'languages':alert['lang']} )
    def start(self):
        self.t.start()
    def terminate(self):
        self.l.terminate = True
    def checkAlive():
        return self.t.isAlive()
