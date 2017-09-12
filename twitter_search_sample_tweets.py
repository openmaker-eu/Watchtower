import tweepy
from tweepy import OAuthHandler
import link_parser
from requests import head

# Accessing Twitter API
consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P"  # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7"  # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

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
