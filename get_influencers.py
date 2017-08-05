import tweepy #Twitter API helper package
from tweepy import OAuthHandler
from application.Connections import Connection

consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P" # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7" # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def get_influencer(alert_id, alert_keywords_list):
    rank = 1
    print(alert_keywords_list)
    for user in api.search_users(q=alert_keywords_list):
        user_dict = user._json
        user_dict['rank'] = rank
        rank = rank + 1
        Connection.Instance().infDB[str(alert_id)].insert_one(user_dict)


Connection.Instance().cur.execute("select alertid, alertname from alerts;")
alerts = Connection.Instance().cur.fetchall()

print(len(alerts))


for alert in alerts:
    get_influencer(alert[0], alert[1].split(","))
