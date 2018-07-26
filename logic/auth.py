__author__ = ['Enis Simsar']

import hashlib
import uuid
import tweepy
from decouple import config

from application.Connections import Connection

# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


# from http://www.pythoncentral.io/hashing-strings-with-python/
def hash_password(password):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt


# from http://www.pythoncentral.io/hashing-strings-with-python/
def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


def register(username, password, country_code):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM users where username = %s)"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 1, 'message': 'Username already taken.'}

        sql = (
            "SELECT NOT EXISTS (SELECT 1 FROM country_code where country_code = %s)"
        )
        cur.execute(sql, [country_code])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 2, 'message': 'Invalid country code.'}

        password = hash_password(password)

        sql = (
            "INSERT INTO users "
            "(username, password, alertlimit, country_code) "
            "VALUES (%s, %s, %s, %s)"
        )
        cur.execute(sql, [username, password, 5, country_code])

        sql = (
            "SELECT * "
            "FROM users "
            "WHERE username = %s"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchall()

        return {'response': True, 'user_id': fetched[0][0]}



def login(username, password):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM users "
            "WHERE username = %s"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchall()
        if len(fetched) == 0:
            return {'response': False, 'error_type': 1, 'message': 'Invalid username'}

        if not check_password(fetched[0][2], str(password)):
            return {'response': False, 'error_type': 2, 'message': 'Invalid password'}

        return {'response': True, 'user_id': fetched[0][0]}

