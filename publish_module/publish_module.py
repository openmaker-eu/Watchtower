from decouple import config
from datetime import datetime
from time import sleep
import sys
import tweepy
import json

sys.path.insert(0, '/root/cloud')

from application.Connections import Connection


def get_twitter_api(access_token, access_token_secret):
    access_token = access_token
    access_token_secret = access_token_secret
    consumer_key = config("TWITTER_CONSUMER_KEY")
    consumer_secret = config("TWITTER_CONSUMER_SECRET")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


def get_users():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT user_id "
            "FROM users;"
        )
        cur.execute(sql, [])
        var = cur.fetchall()

        user_ids = [i[0] for i in var]
        return user_ids


def get_tokens(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_twitter where user_id = %s)"
        )
        cur.execute(sql, [int(user_id)])
        fetched = cur.fetchone()
        if fetched[0]:
            sql = (
                "SELECT access_token, access_token_secret, twitter_id "
                "FROM user_twitter "
                "WHERE user_id = %s;"
            )
            cur.execute(sql, [user_id])
            tokens = cur.fetchone()
            return {'response': True, 'tokens': tokens}
        return {'response': False}


def publish_tweet(topic_id, tweet, url, access_token, access_token_secret):
    api = get_twitter_api(access_token, access_token_secret)
    text = tweet['body'] + " " + url
    try:
        s = api.update_status(text)
        id_str = s.id_str
        original_tweet = s._json
        link = "https://twitter.com/statuses/" + id_str
        Connection.Instance().tweetsDB[str(topic_id)].update_one(
            {'tweet_id': tweet['tweet_id']}, {'$set': {'status': 1, 'tweet_link': link, 'tweet': original_tweet}}, upsert=True)
    except Exception as e:
        print(e)
        Connection.Instance().tweetsDB[str(topic_id)].update_one(
            {'tweet_id': tweet['tweet_id']}, {'$set': {'status': -1}}, upsert=True)
        pass


def main():
    while True:
        users = get_users()
        for user_id in users:
            tokens = get_tokens(user_id)
            if tokens['response']:
                tokens = tokens['tokens']
                for topic_id in Connection.Instance().tweetsDB.collection_names():
                    if topic_id == 'counters':
                        continue
                    tweets = list(
                        Connection.Instance().tweetsDB[str(topic_id)].find(
                            {'published_at': {'$lte': datetime.now()}, 'user_id': str(user_id), 'twitter_id': tokens[2],
                             'status': 0}))
                    for tweet in tweets:
                        print("Publishing tweet_id: {0} and topic_id: {1}".format(tweet['tweet_id'], topic_id))
                        url = "{0}redirect?topic_id={1}&tweet_id={2}".format(config("HOST_URL"), topic_id,
                                                                             tweet['tweet_id'])
                        publish_tweet(topic_id, tweet, url, tokens[0], tokens[1])
        sleep(300)


if __name__ == "__main__":
    main()
