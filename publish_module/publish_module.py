from decouple import config
from datetime import datetime
import sys
import tweepy

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


def get_user_topics(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        own_topic_ids = [i[0] for i in var]

        sql = (
            "SELECT topic_id FROM user_topic_subscribe WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        subscribe_topic_ids = [i[0] for i in var]

        all_topics = set(own_topic_ids + subscribe_topic_ids)

        return all_topics


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
                "SELECT access_token, access_token_secret "
                "FROM user_twitter "
                "WHERE user_id = %s;"
            )
            cur.execute(sql, [user_id])
            tokens = cur.fetchone()
            return {'response': True, 'tokens': tokens}
        return {'response': False}


def publish_tweet(tweet, access_token, access_token_secret):
    api = get_twitter_api(access_token, access_token_secret)
    text = tweet['body'] + " " + tweet['url']
    try:
        api.update_status(text)
        return True
    except:
        pass
    return False


def main():
    while True:
        users = get_users()
        for user_id in users:
            tokens = get_tokens(user_id)
            if tokens['response']:
                tokens = tokens['tokens']
                user_topics = get_user_topics(user_id)
                for topic_id in user_topics:
                    tweets = list(
                        Connection.Instance().tweetsDB[str(topic_id)].find({'published_at': {'$lte': datetime.now()}}))
                    for tweet in tweets:
                        if publish_tweet(tweet, tokens[0], tokens[1]):
                            Connection.Instance().tweetsDB[str(topic_id)].update_one(
                                {'tweet_id': tweet['tweet_id']}, {'status': {'$set': 1}})
                        else:
                            Connection.Instance().tweetsDB[str(topic_id)].update_one(
                                {'tweet_id': tweet['tweet_id']}, {'status': {'$set': -1}})
        sleep(300)


if __name__ == "__main__":
    main()
