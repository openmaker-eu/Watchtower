__author__ = ['Enis Simsar']

import tweepy
from decouple import config
from application.Connections import Connection


def get_user(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT username, country_code "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        fetched = cur.fetchone()

        country = ""
        if fetched[1] is not None:
            country = fetched[1]

        return {'username': fetched[0], 'country': country}

def update_twitter_auth(user_id, auth_token, twitter_pin):
    with Connection.Instance().get_cursor() as cur:
        consumer_key = config("TWITTER_CONSUMER_KEY")
        consumer_secret = config("TWITTER_CONSUMER_SECRET")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.request_token = eval(auth_token)
        auth.secure = True
        token = auth.get_access_token(verifier=twitter_pin)

        if twitter_pin != '' and len(token) == 2:
            auth.set_access_token(token[0], token[1])
            api = tweepy.API(auth)
            user = api.me()._json

            profile_image_url = user['profile_image_url_https']
            screen_name = user['screen_name']
            user_name = user['name']
            twitter_id = user['id_str']

            sql = (
                "SELECT NOT EXISTS (SELECT 1 FROM user_twitter where user_id = %s)"
            )
            cur.execute(sql, [user_id])
            fetched = cur.fetchone()

            if fetched[0]:
                sql = (
                    "INSERT INTO user_twitter "
                    "(user_id, access_token, access_token_secret, profile_image_url, user_name, screen_name, twitter_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )
                cur.execute(sql,
                            [user_id, token[0], token[1], profile_image_url, user_name, screen_name, twitter_id])
            else:
                sql = (
                    "UPDATE user_twitter "
                    "SET access_token = %s, access_token_secret = %s, profile_image_url = %s, "
                    "user_name = %s, screen_name = %s, twitter_id = %s "
                    "WHERE user_id = %s"
                )
                cur.execute(sql,
                            [token[0], token[1], profile_image_url, user_name, screen_name, twitter_id, user_id])

        return {'response': True}

def update_user(user_id, password, country_code, auth_token, twitter_pin):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT NOT EXISTS (SELECT 1 FROM country_code where country_code = %s)"
        )
        cur.execute(sql, [country_code])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 1, 'message': 'Invalid country code.'}

        consumer_key = config("TWITTER_CONSUMER_KEY")
        consumer_secret = config("TWITTER_CONSUMER_SECRET")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.request_token = eval(auth_token)
        auth.secure = True
        token = auth.get_access_token(verifier=twitter_pin)

        if twitter_pin != '' and len(token) == 2:
            auth.set_access_token(token[0], token[1])
            api = tweepy.API(auth)
            user = api.me()._json

            profile_image_url = user['profile_image_url_https']
            screen_name = user['screen_name']
            user_name = user['name']
            twitter_id = user['id_str']

            sql = (
                "SELECT NOT EXISTS (SELECT 1 FROM user_twitter where user_id = %s)"
            )
            cur.execute(sql, [user_id])
            fetched = cur.fetchone()

            if fetched[0]:
                sql = (
                    "INSERT INTO user_twitter "
                    "(user_id, access_token, access_token_secret, profile_image_url, user_name, screen_name, twitter_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )
                cur.execute(sql,
                            [user_id, token[0], token[1], profile_image_url, user_name, screen_name, twitter_id])
            else:
                sql = (
                    "UPDATE user_twitter "
                    "SET access_token = %s, access_token_secret = %s, profile_image_url = %s, "
                    "user_name = %s, screen_name = %s, twitter_id = %s "
                    "WHERE user_id = %s"
                )
                cur.execute(sql,
                            [token[0], token[1], profile_image_url, user_name, screen_name, twitter_id, user_id])
        else:
            sql = (
                "UPDATE users "
                "SET password = %s, country_code = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [password, country_code, user_id])

        return {'response': True}


def set_current_topic(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        topics = cur.fetchall()
        sql = (
            "SELECT topic_id "
            "FROM user_topic_subscribe "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        subscribed_topics = cur.fetchall()
        topics = topics + subscribed_topics
        sql = (
            "SELECT current_topic_id "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user = cur.fetchall()
        if user[0][0] is None and len(topics) != 0:
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [topics[0][0], int(user_id)])
        elif len(topics) == 0:
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [None, int(user_id)])


def get_current_location(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT current_location "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user_location = cur.fetchone()
        if user_location[0] is None:
            sql = (
                "UPDATE users "
                "SET current_location = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, ['italy', int(user_id)])
            return 'italy'
        return user_location[0]


def save_topic_id(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE users "
            "SET current_topic_id = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(topic_id), int(user_id)])


def save_location(location, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE users "
            "SET current_location = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [location, int(user_id)])


def get_current_topic(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT current_topic_id "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user = cur.fetchall()
        if user[0][0] is not None:
            sql = (
                "SELECT topic_id, topic_name "
                "FROM topics "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [int(user[0][0])])
            topic = cur.fetchall()
            return {'topic_id': topic[0][0], 'topic_name': topic[0][1]}
        else:
            return None


def get_twitter_auth_url():
    consumer_key = config("TWITTER_CONSUMER_KEY")
    consumer_secret = config("TWITTER_CONSUMER_SECRET")

    # authenticating twitter consumer key
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    return auth.get_authorization_url(), auth.request_token


def get_topic_limit(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT alertlimit "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        fetched = cur.fetchall()
        return fetched[0][0]


def set_user_topics_limit(user_id, set_type):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT alertlimit "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        fetched = cur.fetchall()
        new_limit = fetched[0][0]
        if set_type == 'decrement':
            new_limit = fetched[0][0] - 1
        elif set_type == 'increment':
            new_limit = fetched[0][0] + 1

        sql = (
            "UPDATE users "
            "SET alertlimit = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [new_limit, int(user_id)])