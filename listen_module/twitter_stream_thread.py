# Import the necessary methods from tweepy library
import json
import re
import sys
import threading
from datetime import datetime

sys.path.append('./')

from bson.objectid import ObjectId
from decouple import config
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
from models.Topic import Topic

from application.Connections import Connection


def get_info(topic_dic):
    keywords = []
    topics = []
    lang = []
    for key in topic_dic:
        topic = topic_dic[key]
        topics = topics + [topic['topic_id']]
        keywords = keywords + topic['keywords']
        lang = lang + topic['lang']
    lang = list(set(lang))
    lang = [str(l) for l in lang]
    keywords = list(set(keywords))
    keywords = [str(keyword) for keyword in keywords]
    result = {
        'topics': sorted(topics),
        'keywords': keywords,
        'lang': lang
    }
    return result


def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
        query={'_id': "tweetDBId"},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return cursor['seq']


def separates_tweet(topic_dic, tweet):
    try:
        for key in topic_dic:
            topic = topic_dic[key]
            if tweet['lang'] in topic['lang']:
                for keyword in topic['keywords']:
                    keyword = re.compile(keyword.replace(" ", "(.?)"), re.IGNORECASE)
                    tweet['tweetDBId'] = get_next_tweets_sequence()
                    if 'extended_tweet' in tweet and 'full_text' in tweet['extended_tweet']:
                        if re.search(keyword, str(tweet['extended_tweet']['full_text'])):
                            updated_time = datetime.fromtimestamp(int(tweet['timestamp_ms']) / 1e3)
                            Topic.update_by_id({'last_tweet_date': updated_time}, topic['topic_id'])
                            tweet['_id'] = ObjectId()
                            if tweet['entities']['urls']:
                                tweet['redis'] = False
                            else:
                                tweet['redis'] = True
                            Connection.Instance().db[str(topic['topic_id'])].insert_one(tweet)
                            break
                    else:
                        if re.search(keyword, str(tweet['text'])):
                            updated_time = datetime.fromtimestamp(int(tweet['timestamp_ms']) / 1e3)
                            Topic.update_by_id({'last_tweet_date': updated_time}, topic['topic_id'])
                            tweet['_id'] = ObjectId()
                            if tweet['entities']['urls'] == [] or tweet['entities']['urls'][0]['expanded_url'] is None:
                                tweet['redis'] = True
                            else:
                                tweet['redis'] = False
                            Connection.Instance().db[str(topic['topic_id'])].insert_one(tweet)
                            break
    except Exception as e:
        pass


# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, topic_dic):
        self.topic_dic = topic_dic
        self.terminate = False
        self.connection = True
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if not self.terminate:
            try:
                tweet = json.loads(data)
                separates_tweet(self.topic_dic, tweet)
                return True
            except Exception as e:
                pass
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
        return True  # To continue listening


class StreamCreator():
    def __init__(self, topic_dic):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(topic_dic)

        self.info = get_info(topic_dic=topic_dic)
        self.keywords = self.info['keywords']
        self.lang = self.info['lang']
        self.alerts = self.info['topics']
        print(self.alerts)
        print(self.keywords)
        print(self.lang)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target=self.stream.filter,
                                  kwargs={'track': self.keywords, 'languages': self.lang, 'stall_warnings': True})

    def start(self):
        self.t.deamon = True
        self.t.start()

    def terminate(self):
        self.l.running = False
        self.l.stop()
        self.l.terminate = True
