import tweepy
from tweepy import OAuthHandler
import link_parser
from requests import head

from decouple import config


consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def unshorten_url(url):
    return head(url, allow_redirects=True).url

def getNewsFromTweets(keywords, languages):
    news = []
    data = tweepy.Cursor(api.search, q=keywords, lang=languages).items(25)
    for tweet in data:
        try:
            temp = tweet._json
            if temp['entities']['urls'] != []:
                link = temp['entities']['urls'][0]['expanded_url']
                if link is not None:
                    parsed_link = link_parser.linkParser(unshorten_url(link))
                    if parsed_link is not None:
                        news.append(parsed_link)
                        if len(news) >= 3:
                            break
        except:
            pass
    return list(news)
