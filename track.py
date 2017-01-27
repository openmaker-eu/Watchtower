#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import time
import threading
import dbM
import json

def get_next_tweets_sequence(zimdB):
    cursor = self.db_listener["counters"].find_and_modify(
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

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def __init__(self,alert):
        self.terminate = False
        self.campaignId = alert['id']
        self.campaignName = alert['name']
        self.dbName = 'openMakerdB'
        self.c_connect = dbM.connection_try() #try to connect pymongo
        self.db_listener = dbM.handle_db(self.c_connect,self.dbName) #handle a database
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            #print data
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence(self.db_listener)
            self.db_listener[str(self.campaignId)].insert_one(tweet) #this creates tweets collection, if there is one then write on it
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
