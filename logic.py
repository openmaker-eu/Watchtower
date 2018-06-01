import csv
import hashlib
import json
import re
import time
import uuid
from threading import Thread
from urllib.parse import urlparse
from datetime import datetime, timedelta

import facebook
import praw
import psycopg2
import pymongo
import requests
import tweepy
from decouple import config

import delete_community
from application.Connections import Connection
from application.utils import general
from application.utils import twitter_search_sample_tweets
from crontab_module.crons import facebook_reddit_crontab

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


def add_facebook_pages_and_subreddits(topic_id, topic_list):
    print(topic_list)
    sources = source_selection(topic_list)
    with Connection.Instance().get_cursor() as cur:
        for facebook_page_id in sources['pages']:
            sql = (
                "INSERT INTO topic_facebook_page "
                "(topic_id, facebook_page_id) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(topic_id), facebook_page_id['page_id']])

        for subreddit in sources['subreddits']:
            sql = (
                "INSERT INTO topic_subreddit "
                "(topic_id, subreddit) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(topic_id), subreddit])

    pages = [facebook_page_id['page_id'] for facebook_page_id in sources['pages']]
    subreddits = [subreddit for subreddit in sources['subreddits']]
    facebook_reddit_crontab.triggerOneTopic(topic_id, topic_list, list(set(pages)), list(set(subreddits)))


def source_selection(topic_list):
    return {'pages': source_selection_from_facebook(topic_list),
            'subreddits': source_selection_from_reddit(topic_list)}


def source_selection_from_facebook(topic_list):
    my_token = config("FACEBOOK_TOKEN")
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")
    pages = []
    for topic in topic_list:
        s = graph.get_object("search?q=" + topic + "&type=page&limit=3")
        for search in s["data"]:
            pages.append({"page_id": search["id"], "page_name": search["name"]})
        s = graph.get_object("search?q=" + topic + "&type=group&limit=3")
        for search in s["data"]:
            if search["privacy"] == "OPEN":
                pages.append({"page_id": search["id"], "page_name": search["name"]})
    return [i for n, i in enumerate(pages) if i not in pages[n + 1:]]


def source_selection_from_reddit(topic_list):
    keys = {
        'client_id': config("REDDIT_CLIENT_ID"),
        'client_secret': config("REDDIT_CLIENT_SECRET"),
        'user_agent': config("REDDIT_USER_AGENT"),
        'api_type': 'json'
    }
    reddit = praw.Reddit(client_id=keys["client_id"],
                         client_secret=keys["client_secret"],
                         user_agent=keys["user_agent"],
                         api_type=keys["api_type"])
    all_subreddits = []
    for topic in topic_list:
        subreddits = reddit.subreddits.search_by_name(topic)
        if " " in topic:
            subreddits.extend(reddit.subreddits.search_by_name(topic.replace(" ", "_")))
            subreddits.extend(reddit.subreddits.search_by_name(topic.replace(" ", "")))
        subreddits = set([sub.display_name for sub in subreddits])
        all_subreddits = list(set(all_subreddits + list(subreddits)))
    return all_subreddits


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
                cur.execute(sql, [user_id, token[0], token[1], profile_image_url, user_name, screen_name, twitter_id])
            else:
                sql = (
                    "UPDATE user_twitter "
                    "SET access_token = %s, access_token_secret = %s, profile_image_url = %s, "
                    "user_name = %s, screen_name = %s, twitter_id = %s "
                    "WHERE user_id = %s"
                )
                cur.execute(sql, [token[0], token[1], profile_image_url, user_name, screen_name, twitter_id, user_id])

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
                cur.execute(sql, [user_id, token[0], token[1], profile_image_url, user_name, screen_name, twitter_id])
            else:
                sql = (
                    "UPDATE user_twitter "
                    "SET access_token = %s, access_token_secret = %s, profile_image_url = %s, "
                    "user_name = %s, screen_name = %s, twitter_id = %s "
                    "WHERE user_id = %s"
                )
                cur.execute(sql, [token[0], token[1], profile_image_url, user_name, screen_name, twitter_id, user_id])
        else:
            sql = (
                "UPDATE users "
                "SET password = %s, country_code = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [password, country_code, user_id])

        return {'response': True}


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


def get_all_running_topics_list():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE is_running = %s"
        )
        cur.execute(sql, [True])
        var = cur.fetchall()
        alerts = [
            {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': sorted(i[3].split(",")),
             'lang': sorted(i[4].split(","))}
            for i in var]
        return sorted(alerts, key=lambda k: k['alertid'])


def get_topic_list(user_id):
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

        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id != %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        remaining_topics_topics = []
        for i in var:
            if i[0] not in subscribe_topic_ids:
                remaining_topics_topics.append(i[0])

        sql = (
            "SELECT * "
            "FROM topics;"
        )
        cur.execute(sql)
        var = cur.fetchall()

        topics = []

        for i in var:
            sql = (
                "SELECT user_id FROM user_topic WHERE topic_id = %s ;"
            )
            cur.execute(sql, [i[0]])
            var = cur.fetchone()
            sql = (
                "SELECT username FROM users WHERE user_id = %s ;"
            )
            cur.execute(sql, [var[0]])
            var = cur.fetchone()
            temp_topic = {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': i[3].split(","),
                          'lang': i[4].split(","), 'creationTime': i[5], 'updatedTime': i[7], 'status': i[8],
                          'publish': i[9], 'newsUpdatedTime': i[10], 'created_by': var[0]}
            if i[0] in own_topic_ids:
                temp_topic['type'] = 'me'
            elif i[0] in subscribe_topic_ids:
                temp_topic['type'] = 'subscribed'
            elif i[0] in remaining_topics_topics:
                temp_topic['type'] = 'unsubscribed'
            topics.append(temp_topic)

        topics = sorted(topics, key=lambda k: k['alertid'])
        for topic in topics:
            topic['newsCount'] = Connection.Instance().newsPoolDB[str(topic['alertid'])].find().count()
            topic['audienceCount'] = Connection.Instance().audienceDB[str(topic['alertid'])].find().count()
            topic['eventCount'] = Connection.Instance().events[str(topic['alertid'])].find().count()
            topic['tweetCount'] = Connection.Instance().db[str(topic['alertid'])].find().count()
            try:
                hash_tags = list(Connection.Instance().hashtags[str(topic['alertid'])].find({'name': 'month'},
                                                                                            {'month': 1, 'count': 1,
                                                                                             '_id': 0}))[0]['month']
            except:
                hash_tags = []
                pass
            sql = (
                "SELECT ARRAY_AGG(hashtag) FROM topic_hashtag WHERE topic_id = %s ;"
            )
            cur.execute(sql, [topic['alertid']])
            var = cur.fetchone()
            tags = var[0] if var[0] is not None else []
            hash_tags = [
                {'hashtag': hash_tag['hashtag'], 'count': hash_tag['count'], 'active': hash_tag['hashtag'] not in tags}
                for hash_tag in hash_tags]
            topic['hashtags'] = hash_tags

        topics.sort(key=lambda topic: (topic['publish'], topic['newsCount']), reverse=True)
        return topics


def topic_exist(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchone()
        if var is not None:
            return True
        else:
            return False


def get_topic(topic_id):
    if topic_id is not None:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT * "
                "FROM topics "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchone()
            topic = {'alertid': var[0], 'name': var[1], 'description': var[2], 'keywords': var[3],
                     'lang': var[4].split(","), 'status': var[8],
                     'keywordlimit': var[6]}
    else:
        topic = {'alertid': "", 'name': "", 'keywords': "", 'lang': "", 'status': False, 'keywordlimit': 20,
                 'description': ""}
    return topic


def get_topic_all_of_them_list(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        var = cur.fetchone()
        print(var)
        topic = {'alertid': var[0], 'name': var[1], 'keywords': var[3].split(","), 'lang': var[4].split(","),
                 'status': var[8]}
        return topic


def set_user_topics_imit(user_id, set_type):
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


def ban_domain(user_id, topic_id, domain):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_domain where user_id = %s and domain = %s)"
        )
        cur.execute(sql, [int(user_id), domain])
        fetched = cur.fetchone()

        if not fetched[0]:
            sql = (
                "INSERT INTO user_domain "
                "(user_id, domain) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [user_id, domain])
            Connection.Instance().filteredNewsPoolDB[str(topic_id)].update_many(
                {},
                {'$pull': {
                    'yesterday': {'domain': domain},
                    'week': {'domain': domain},
                    'month': {'domain': domain}
                }},
                upsert=True
            )


def add_topic(topic, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO topics "
            "(topic_name, topic_description, keywords, languages, keyword_limit) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cur.execute(sql, [topic['name'], topic['description'], topic['keywords'], topic['lang'], topic['keywordlimit']])
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            "ORDER BY topic_id DESC "
            "LIMIT 1"
        )
        cur.execute(sql)
        topic_fetched = cur.fetchone()
        print(topic_fetched)

    if topic['name'] == topic_fetched[1]:
        sql = (
            "INSERT INTO user_topic "
            "(user_id, topic_id) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_fetched[0])])
        topic = get_topic_all_of_them_list(int(topic_fetched[0]))
        set_user_topics_imit(user_id, 'decrement')
        set_current_topic(user_id)
        t = Thread(target=add_facebook_pages_and_subreddits, args=(topic_fetched[1], topic['keywords'],))
        t.start()


def delete_topic(topic_id, user_id):
    alert = get_topic_all_of_them_list(topic_id)
    set_user_topics_imit(user_id, 'increment')
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        topic = cur.fetchone()
        topic = list(topic)
        topic.append(int(user_id))
        sql = (
            "INSERT INTO public.archived_topics "
            "(topic_id, topic_name, topic_description, keywords, languages, creation_time, "
            "keyword_limit, last_tweet_date, is_running, is_publish, user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        )
        cur.execute(sql,
                    [topic[0], topic[1], topic[2], topic[3], topic[4], topic[5], topic[6], topic[7], topic[8], topic[9],
                     int(user_id)])
        sql = (
            "DELETE FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        sql = (
            "DELETE FROM user_topic "
            "WHERE topic_id = %s AND user_id = %s"
        )
        cur.execute(sql, [topic_id, user_id])
        sql = (
            "DELETE FROM topic_facebook_page "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        sql = (
            "DELETE FROM topic_subreddit "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
    set_current_topic(user_id)

    t = Thread(target=delete_community.main, args=(alert['alertid'],))
    t.start()


def update_topic(topic):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET topic_description = %s, keywords = %s, languages = %s, keyword_limit = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql,
                    [topic['description'], topic['keywords'], topic['lang'], topic['keywordlimit'], topic['alertid']])
    topic = get_topic_all_of_them_list(topic['alertid'])
    t = Thread(target=add_facebook_pages_and_subreddits, args=(topic['alertid'], topic['keywords'],))
    t.start()


def start_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, topic_id])


def stop_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, topic_id])


def publish_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, topic_id])


def unpublish_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, topic_id])


def get_bookmarks(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT bookmark_link_id "
            "FROM user_bookmark "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        bookmark_link_ids = [a[0] for a in cur.fetchall()]

        if len(bookmark_link_ids) == 0:
            bookmark_link_ids = [-1]

        sql = (
            "SELECT news_id, rating "
            "FROM user_news_rating "
            "WHERE user_id = %s and news_id IN %s"
        )
        cur.execute(sql, [int(user_id), tuple(bookmark_link_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

        news = []
        for alertid in Connection.Instance().newsPoolDB.collection_names():
            news = news + list(
                Connection.Instance().newsPoolDB[str(alertid)].find({'link_id': {'$in': bookmark_link_ids}}))

        for news_item in news:
            news_item['bookmark'] = True

            news_item['sentiment'] = 0
            try:
                news_item['sentiment'] = ratings[str(news_item['link_id'])]
            except KeyError:
                pass

        return news


def add_bookmark(user_id, link_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO user_bookmark "
            "(user_id, bookmark_link_id) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [int(user_id), int(link_id)])


def remove_bookmark(user_id, link_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "DELETE FROM user_bookmark "
            "WHERE user_id = %s AND bookmark_link_id = %s"
        )
        cur.execute(sql, [int(user_id), int(link_id)])


def sentiment_news(topic_id, user_id, link_id, rating):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_news_rating where user_id = %s and topic_id = %s and news_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id), int(link_id)])
        fetched = cur.fetchone()

        if fetched[0]:
            sql = (
                "UPDATE user_news_rating "
                "SET rating = %s "
                "WHERE user_id = %s and news_id = %s and topic_id = %s"
            )
            cur.execute(sql, [float(rating), int(user_id), int(link_id), int(topic_id)])
        else:
            sql = (
                "INSERT INTO user_news_rating "
                "(user_id, news_id, topic_id, rating) "
                "VALUES (%s, %s, %s, %s)"
            )
            cur.execute(sql, [int(user_id), int(link_id), int(topic_id), float(rating)])


def rate_audience(topic_id, user_id, audience_id, rating):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS "
            "(SELECT 1 FROM user_audience_rating where user_id = %s and topic_id = %s and audience_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id), int(audience_id)])
        fetched = cur.fetchone()

        if fetched[0]:
            if float(rating) != 0.0:
                sql = (
                    "UPDATE user_audience_rating "
                    "SET rating = %s "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [float(rating), int(user_id), int(audience_id), int(topic_id)])
            else:
                sql = (
                    "DELETE FROM user_audience_rating "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id)])
        else:
            if float(rating) != 0.0:
                sql = (
                    "INSERT INTO user_audience_rating "
                    "(user_id, audience_id, topic_id, rating) "
                    "VALUES (%s, %s, %s, %s)"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id), float(rating)])


def add_local_influencer(topic_id, location, screen_name):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO added_influencers "
            "(topic_id, country_code, screen_name) "
            "VALUES (%s, %s, %s)"
        )
        cur.execute(sql, [int(topic_id), str(location), str(screen_name), ""])

    if Connection.Instance().added_local_influencers_DB['added_influencers'].find_one(
            {"screen_name": screen_name}) is None:
        new_local_influencer = api.get_user(screen_name)
        new_local_influencer['topics'] = topic_id
        new_local_influencer['locations'] = location
        Connection.Instance().added_local_influencers_DB['added_influencers'].insert_one(new_local_influencer)
    else:
        Connection.Instance().added_local_influencers_DB['added_influencers'].update(
            {"screen_name": screen_name},
            {
                "$addToSet": {
                    "topics": topic_id,
                    "locations": location
                }
            }
        )


def hide_influencer(topic_id, user_id, influencer_id, description, is_hide, location):
    # print("in hide influencer:")
    # print(influencer_id)
    print("In hide influencer")
    print("Topic id:" + str(topic_id))
    print("Location:" + location)
    influencer_id = int(influencer_id)
    print(influencer_id)
    if is_hide:
        print("Hiding influencer with ID:" + str(influencer_id))
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "INSERT INTO hidden_influencers "
                "(topic_id, country_code, influencer_id, description) "
                "VALUES (%s, %s, %s, %s)"
            )
            cur.execute(sql, [int(topic_id), str(location), str(influencer_id), ""])
    else:
        print("Unhiding influencer with ID:" + str(influencer_id))
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "DELETE FROM hidden_influencers "
                "WHERE topic_id = %s and country_code = %s and influencer_id = %s "
            )
            cur.execute(sql, [int(topic_id), str(location), str(influencer_id)])


def hide_event(topic_id, user_id, event_link, description, is_hide):
    # print("in hide influencer:")
    # print(influencer_id)
    print("In hide event")
    print("Topic id:" + str(topic_id))
    event_link = str(event_link)
    print(event_link)
    if is_hide:
        print("Hiding event with link:" + event_link)
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "INSERT INTO hidden_events "
                "(topic_id, event_link, description) "
                "VALUES (%s, %s, %s)"
            )
            cur.execute(sql, [int(topic_id), str(event_link), ""])
    else:
        print("Unhiding event with link:" + event_link)
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "DELETE FROM hidden_events "
                "WHERE topic_id = %s and event_link = %s "
            )
            cur.execute(sql, [int(topic_id), str(event_link)])


def get_tweets(topic_id):
    tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                               'created_at': 1, "_id": 0}).sort(
        [('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


def get_skip_tweets(topic_id, last_tweet_id):
    tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$lt': int(last_tweet_id)}},
                                                          {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                           'created_at': 1, "_id": 0}) \
        .sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


def check_tweets(topic_id, newest_id):
    if int(newest_id) == -1:
        tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                   'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$gt': int(newest_id)}},
                                                              {'tweetDBId': 1, "text": 1, "user": 1, 'created_at': 1,
                                                               "_id": 0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)


def get_new_tweets(topic_id, newest_id):
    if int(newest_id) == -1:
        tweets = Connection.Instance().db[str(topic_id)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                   'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(topic_id)].find({'tweetDBId': {'$gt': int(newest_id)}},
                                                              {'tweetDBId': 1, 'id': 1, "text": 1, "user": 1,
                                                               'created_at': 1, "_id": 0}) \
            .sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return tweets


def search_news(keywords, languages):
    keys = keywords.split(",")
    result_keys = []
    for key in keys:
        if " " in key:
            result_keys.append("\"" + key + "\"")
        else:
            result_keys.append(key)
    # ends
    keywords = " OR ".join(result_keys)
    languages = " OR ".join(languages.split(","))
    news = twitter_search_sample_tweets.getNewsFromTweets(keywords, languages)
    return news


def get_news(user_id, topic_id, date, cursor):
    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    feeds = list(Connection.Instance().filteredNewsPoolDB[str(topic_id)].find({'name': date}, {date: 1}))
    link_ids = []
    if len(feeds) != 0:
        feeds = list(feeds[0][date][cursor:cursor + 20])
        link_ids = [news['link_id'] for news in feeds]

    if len(link_ids) == 0:
        link_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT news_id, rating "
            "FROM user_news_rating "
            "WHERE user_id = %s and topic_id = %s and news_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(link_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

        sql = (
            "SELECT bookmark_link_id "
            "FROM user_bookmark "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        bookmarks = [link_id[0] for link_id in cur.fetchall()]

        tweets = list(Connection.Instance().tweetsDB[str(topic_id)].find({'user_id': user_id}, {'news_id': 1}))
        tweets = [link_id['news_id'] if 'news_id' in link_id else -1 for link_id in tweets]

    for feed in feeds:
        feed['bookmark'] = False
        if feed['link_id'] in bookmarks:
            feed['bookmark'] = True

        feed['tweet'] = False
        if feed['link_id'] in tweets:
            feed['tweet'] = True

        feed['sentiment'] = 0
        try:
            feed['sentiment'] = ratings[str(feed['link_id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 20
    if cursor >= 60 or len(feeds) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 60
    result['feeds'] = feeds
    return result


def get_audience(topic_id, user_id, cursor, location):
    print("In get audience")
    if topic_id is None:
        print("Topic is not defined.")
    print("Topic " + str(topic_id))
    print("Location " + str(location))
    print("Cursor " + str(cursor))
    result = {}
    audiences = list(Connection.Instance().audience_samples_DB[str(location) + "_" + str(topic_id)].find({}))[
                cursor:cursor + 21]
    audience_ids = []
    if len(audiences) != 0:
        audience_ids = [audience['id'] for audience in audiences]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for audience in audiences:
        audience['rate'] = 0
        try:
            audience['rate'] = ratings[str(audience['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audiences) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audiences'] = audiences
    return result


def get_audience_stats(topic_id, location):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT execution_duration, last_executed, from_predicted_location, from_regex "
            "FROM audience_samples_last_executed "
            "WHERE topic_id = %(topic_id)s and location = %(location)s "
        )

        params = {
            'topic_id': int(topic_id),
            'location': location,
        }

        cur.execute(sql, params)
        audience_stats = {}

        execution_duration, last_executed, from_predicted_location, from_regex = cur.fetchall()[0]

        audience_stats['topic_id'] = int(topic_id)
        audience_stats['location'] = str(location)
        audience_stats['execution_duration'] = round(execution_duration.total_seconds(), 2)
        audience_stats['last_executed'] = last_executed.date()
        audience_stats['from_predicted_location'] = from_predicted_location
        audience_stats['from_regex'] = from_regex

        return audience_stats


def get_events(topic_id, sortedBy, location, cursor):
    cursor_range = 10
    max_cursor = 100
    cursor = int(cursor)
    result = {}
    events = []
    location = location.lower()
    if cursor >= max_cursor:
        result['events'] = []
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result
    try:
        topic_id = int(topic_id)
    except:
        result['event'] = "topic not found"
        return result
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_name "
            "FROM topics "
            "WHERE topic_id = %s;"
        )
        try:
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]
        except:
            result['error'] = "Topic does not exist."
            return result

        events = []  # all events to be returned
        match = {'end_time': {'$gte': time.time()}}
        sort = {}

        result['topic'] = topic_name
        result['location'] = location

    # SORT CRITERIA
    if sortedBy == 'interested':
        sort['interested'] = -1
    elif sortedBy == 'date' or sortedBy == '':
        sort['start_time'] = 1
    else:
        return {'error': "please enter a valid sortedBy value."}

    print("Location: " + str(location))
    if location != "" and location.lower() != "global":
        # location_predictor = Predictor()
        # location = location_predictor.predict_location(location)
        if location == "italy":
            location = "it"
        elif location == "spain":
            location = "es"
        elif location == "slovakia":
            location = "sk"
        elif location == "uk":
            location = "gb"
        elif location == "turkey":
            location = "tr"

        print("Filtering and sorting by location: " + location)
        EVENT_LIMIT = 70
        COUNTRY_LIMIT = 80
        cdl = []

        with open('rank_countries.csv', 'r') as f:
            reader = csv.reader(f)
            country_distance_lists = list(reader)
            for i in range(len(country_distance_lists)):
                if country_distance_lists[i][0] == location:
                    cdl = country_distance_lists[i]
            print("Found cdl!")
        count = 0
        for country in cdl[1:]:
            match['$or'] = [{'place': re.compile("^.*\\b" + country + "$", re.IGNORECASE)},
                            {'predicted_place': country}]
            events_in_current_location = list(Connection.Instance().events[str(topic_id)].aggregate([
                {'$match': match},
                {'$project': {'_id': 0,
                              "updated_time": 1,
                              "cover": 1,
                              "end_time": 1,
                              "description": 1,
                              "start_date": 1,
                              "end_date": 1,
                              "id": 1,
                              "name": 1,
                              "place": 1,
                              "start_time": 1,
                              "link": 1,
                              "interested": 1,
                              "coming": 1
                              }},
                {'$sort': sort}
                # {'$skip': int(cursor)},
                # {'$limit': 10}
            ]))
            events += events_in_current_location
            count += 1
            message = "Checked db for country (#" + str(count) + "): " + str(country)
            if len(events_in_current_location) > 0:
                message += " + " + str(len(events_in_current_location)) + " events!"

            print(message)

            print("length:" + str(len(events)))
            if len(events) >= min(cursor + cursor_range, EVENT_LIMIT):
                break
            if (count > COUNTRY_LIMIT):
                print("Searched closest " + str(COUNTRY_LIMIT) + " countries. Stopping here.")
                break

        # pprint.pprint([e['place'] for e in events])
        display_events = events[cursor:min(cursor + cursor_range, max_cursor)]

        result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
        if cursor != 0: result[
            'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

        # cursor boundary checks
        if result['next_cursor'] >= min(EVENT_LIMIT, max_cursor) or len(display_events) < cursor_range:
            result['next_cursor'] = 0
        if 'previous_cursor' in result:
            if result['previous_cursor'] == 0:
                result['previous_cursor'] = -1

        result['next_cursor_str'] = str(result['next_cursor'])
        result['events'] = display_events

    else:
        print("returning all events...")
        events = list(Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': match},
            {'$project': {'_id': 0,
                          "updated_time": 1,
                          "cover": 1,
                          "end_time": 1,
                          "description": 1,
                          "start_date": 1,
                          "end_date": 1,
                          "id": 1,
                          "name": 1,
                          "place": 1,
                          "start_time": 1,
                          "link": 1,
                          "interested": 1,
                          "coming": 1
                          }},
            {'$sort': sort},
            {'$skip': int(cursor)},
            {'$limit': min(cursor_range, max_cursor - cursor)}
        ]))

        cursor = int(cursor)
        result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
        if cursor != 0: result[
            'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

        # cursor boundary checks
        if result['next_cursor'] >= max_cursor or len(events) < cursor_range:
            result['next_cursor'] = 0
        if 'previous_cursor' in result:
            if result['previous_cursor'] == 0:
                result['previous_cursor'] = -1

        result['next_cursor_str'] = str(result['next_cursor'])
        result['events'] = events

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT event_link "
            "FROM hidden_events "
            "WHERE topic_id = %s "
        )
        cur.execute(sql, [int(topic_id)])
        hidden_links = [str(event_link[0]) for event_link in cur.fetchall()]
        # print("Hidden ids:")
        # print(hidden_ids)
        for event in result['events']:
            if str(event['link']) in hidden_links:
                # print(str(event['link']) + " is hidden")
                event['hidden'] = True
            else:
                event['hidden'] = False
                # print(str(event['link']) + " not hidden")

    for event in result['events']:
        if not isinstance(event['start_time'], str):
            event['start_time'] = datetime.utcfromtimestamp(event['start_time']).strftime('%Y-%m-%dT%H:%M:%SZ')
        if not isinstance(event['end_time'], str):
            event['end_time'] = datetime.utcfromtimestamp(event['end_time']).strftime('%Y-%m-%dT%H:%M:%SZ')

    return result


def add_or_delete_fetch_followers_job(user_id, influencer_id, fetching):
    status = "created"
    print(str(user_id))
    print(str(influencer_id))
    if fetching:
        print("Adding fetch followers for influencer: " + str(influencer_id) + " to job queue")
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "INSERT INTO fetch_followers_job_queue "
                "VALUES (%(user_id)s, %(influencer_id)s, %(creation_time)s, %(status)s) "
            )

            params = {
                'user_id': int(user_id),
                'influencer_id': str(influencer_id),
                'creation_time': datetime.utcnow(),
                'status': status,
            }

            try:
                cur.execute(sql, params)
            except psycopg2.OperationalError as e:
                print('Unable to connect!\n{0}').format(e)
    else:
        print("Deleting fetch followers job for influencer:" + str(influencer_id))
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "DELETE FROM fetch_followers_job_queue "
                "WHERE influencer_id = %s "
            )
            cur.execute(sql, [str(influencer_id)])


def get_local_influencers(topic_id, cursor, location):
    print("In get local infs")
    print("Topic id: " + str(topic_id))
    print("Location: " + location)
    result = {}
    local_influencers = []

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT influencer_id "
            "FROM hidden_influencers "
            "WHERE country_code = %s and topic_id = %s "
        )
        cur.execute(sql, [str(location), int(topic_id)])
        hidden_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]
        # print("Hidden ids:")
        # print(hidden_ids)

    if location.lower() == "global":
        local_influencers += list(Connection.Instance().influencerDB["all_influencers"].find({"topics": topic_id}))[
                             cursor:cursor + 21]
    else:
        local_influencers += list(
            Connection.Instance().local_influencers_DB[str(topic_id) + "_" + str(location)].find({}))[
                             cursor:cursor + 21]

    for inf in local_influencers:
        inf['id'] = str(inf['id'])

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT influencer_id "
            "FROM hidden_influencers "
            "WHERE country_code = %s and topic_id = %s "
        )
        cur.execute(sql, [str(location), int(topic_id)])
        hidden_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]

        sql = (
            "SELECT influencer_id "
            "FROM fetch_followers_job_queue "
        )
        cur.execute(sql)
        fetching_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]

        for influencer in local_influencers:
            if str(influencer['id']) in hidden_ids:
                influencer['hidden'] = True
            else:
                influencer['hidden'] = False
            if str(influencer['id']) in fetching_ids:
                influencer['in_fetch_followers_queue'] = True
            else:
                influencer['in_fetch_followers_queue'] = False

    # Convert last refreshed and last processed to date from datetime for readability
    for influencer in local_influencers:
        if 'last_refreshed' in influencer:
            dt = influencer['last_refreshed']
            influencer['last_refreshed'] = dt.date()
        if 'last_processed' in influencer:
            dt = influencer['last_processed']
            influencer['last_processed'] = dt.date()

    cursor = int(cursor) + 21
    if cursor >= 500 or len(local_influencers) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['local_influencers'] = local_influencers
    return result


def get_recommended_audience(topic_id, location, filter_type, user_id, cursor):
    result = {}
    if filter_type == "rated":
        # fetch rated audience
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT audience_id "
                "FROM user_audience_rating "
                "WHERE user_id = %s and topic_id = %s ;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            rated_audience = cur.fetchall()
            rated_audience = [aud_member[0] for aud_member in rated_audience]
            audience = Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': rated_audience}})

    elif filter_type == "recommended":
        # fetch recommended audience
        audience = Connection.Instance().audience_samples_DB[str(location) + '_' + str(topic_id)].find({})

    else:
        print("Please provide a valid filter. \"rated\" or \"recommended\"")
        return
    audience = list(audience)[cursor:cursor + 21]

    audience_ids = []
    if len(audience) != 0:
        audience_ids = [aud_member['id'] for aud_member in audience]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for aud_member in audience:
        aud_member['rate'] = 0
        try:
            aud_member['rate'] = ratings[str(aud_member['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audience) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audience'] = audience
    return result


def subsribe_topic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()

        if not fetched[0]:
            sql = (
                "INSERT INTO user_topic_subscribe "
                "(user_id, topic_id) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])


def unsubsribe_topic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()
        if fetched[0]:
            sql = (
                "DELETE FROM user_topic_subscribe "
                "WHERE user_id = %s and topic_id = %s;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [None, int(user_id)])


def get_relevant_locations():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM relevant_locations;"
        )
        cur.execute(sql, [])
        locations = cur.fetchall()
        return [{'location_name': i[0], 'location_code': i[1]} for i in locations]


def get_twitter_auth_url():
    consumer_key = config("TWITTER_CONSUMER_KEY")
    consumer_secret = config("TWITTER_CONSUMER_SECRET")

    # authenticating twitter consumer key
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    return auth.get_authorization_url(), auth.request_token


def get_next_tweet_sequence():
    cursor = Connection.Instance().tweetsDB["counters"].find_and_modify(
        query={'_id': "tweet_id"},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return cursor['seq']


def linky(url):
    """Sanitize link. clean utm parameters on link."""
    if not re.match(r'^https?:\/\/', url):
        url = 'http://%s' % url

    rv = urlparse(url)

    if rv.query:
        query = re.sub(r'utm_\w+=[^&]+&?', '', rv.query)
        url = '%s://%s%s?%s' % (rv.scheme, rv.hostname, rv.path, query)

    # remove ? at the end of url
    url = re.sub(r'\?$', '', url)
    return url


def scrape_url(url):
    payload = {'scrape': 'true',
               'id': linky(url),
               'access_token': config("FACEBOOK_TOKEN")}

    print(payload)

    r = requests.post("https://graph.facebook.com/v2.11/", data=payload)

    result = {}
    print(r.text)
    if r.status_code == requests.codes.ok:
        result['response'] = True
        result['data'] = json.loads(r.text)
    else:
        result['response'] = False

    return result


def get_publish_tweet(topic_id, user_id, tweet_id, news_id, date):
    if int(tweet_id) != -1:
        return [Connection.Instance().tweetsDB[str(topic_id)].find_one({'tweet_id': int(tweet_id)})]
    else:
        news = Connection.Instance().newsPoolDB[str(topic_id)].find_one({'link_id': int(news_id)})
        result = scrape_url(news['url'])
        image_url = news['im']
        description = news['summary']
        title = news['title']
        if result['response']:
            data = result['data']
            if 'image' in data and 'url' in data['image'][0]:
                image_url = data['image'][0]['url']
            if 'description' in data:
                description = data['description']
            if 'title' in data:
                title = data['title']
        tweet = {
            'tweet_id': -1,
            'image_url': image_url,
            'body': news['summary'],
            'title': title,
            'source': news['source'],
            'description': description,
            'url': news['url'],
            'published_at': date,
            'status': 0
        }
        return [tweet]


def get_publish_tweets(topic_id, user_id, status):
    tweet_ids = [i['tweet_id'] for i in
                 Connection.Instance().tweetsDB[str(topic_id)].find({'user_id': user_id}, {'tweet_id': 1})]
    tweets = []
    sort_order = pymongo.ASCENDING
    if int(status) == 1:
        sort_order = pymongo.DESCENDING
    for i in Connection.Instance().tweetsDB[str(topic_id)].find(
            {'tweet_id': {'$in': tweet_ids}, 'status': int(status)}).sort([('published_at', sort_order)]):
        temp = i
        temp['published_at'] = general.tweet_date_to_string(i['published_at'])
        tweets.append(temp)
    return tweets


def delete_publish_tweet(topic_id, user_id, tweet_id):
    Connection.Instance().tweetsDB[str(topic_id)].remove({'tweet_id': int(tweet_id)})


def update_publish_tweet(topic_id, user_id, tweet_id, date, text, news_id, title, description, image_url):
    tweet_id = int(tweet_id)
    twitter_user = get_twitter_user(user_id)
    if int(tweet_id) == -1:
        tweet_id = get_next_tweet_sequence()
        news = Connection.Instance().newsPoolDB[str(topic_id)].find_one({'link_id': int(news_id)})
        tweet = {
            'tweet_id': tweet_id,
            'news_id': news['link_id'],
            'user_id': user_id,
            'twitter_id': twitter_user['twitter_id'],
            'body': text,
            'title': title,
            'source': news['source'],
            'description': description,
            'url': news['url'],
            'image_url': image_url,
            'published_at': general.tweet_date_to_string(date),
            'status': 0
        }
        Connection.Instance().tweetsDB[str(topic_id)].insert_one(tweet)
    else:
        tweet = Connection.Instance().tweetsDB[str(topic_id)].find_one({'tweet_id': int(tweet_id)})
        published_at = general.tweet_date_to_string(date)
        if tweet['status'] != 0:
            update_publish_tweet(topic_id, user_id, -1, date, text, tweet['news_id'], title, description, image_url)
        else:
            Connection.Instance().tweetsDB[str(topic_id)].update_one({'tweet_id': tweet_id},
                                                                     {'$set': {'body': text,
                                                                               'published_at': published_at,
                                                                               'user_id': user_id,
                                                                               'twitter_id': twitter_user[
                                                                                   'twitter_id']}})


def get_twitter_user(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_twitter where user_id = %s)"
        )
        cur.execute(sql, [int(user_id)])
        fetched = cur.fetchone()
        if fetched[0]:
            sql = (
                "SELECT user_name, screen_name, profile_image_url, twitter_id "
                "FROM user_twitter "
                "WHERE user_id = %s;"
            )
            cur.execute(sql, [user_id])
            user = cur.fetchone()
            return {'user_name': user[0], 'screen_name': user[1], 'profile_image_url': user[2], 'twitter_id': user[3]}
        return {'user_name': '', 'screen_name': '', 'profile_image_url': '', 'twitter_id': ''}


def get_tweet(topic_id, tweet_id):
    if int(tweet_id) != -1:
        return Connection.Instance().tweetsDB[str(topic_id)].find_one({'tweet_id': int(tweet_id)})
    return []


def get_crons_log():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT cron_name, started_at, ended_at, status, frequency "
            "FROM crons_log "
            "WHERE id IN ("
            "SELECT MAX(id) "
            "FROM crons_log "
            "GROUP BY cron_name"
            ") ORDER BY cron_name;"
        )
        cur.execute(sql, [])
        fetched = cur.fetchall()

        if fetched:
            def get_duration(x, y):
                if y is None: return "-"
                diff = y - x
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60

                if hours == 0 and minutes == 0:
                    return "{0} seconds".format(seconds)
                elif hours == 0:
                    return "{0} min, {1} seconds".format(minutes, seconds)

                return "{0} h, {1} min, {2} sec.".format(hours, minutes, seconds)

            return [{'cron_name': cron[0], 'started_at': cron[1], 'ended_at': cron[2], 'status': cron[3],
                     'duration': get_duration(cron[1], cron[2]), 'frequency': cron[4]} for cron in fetched]

        return []


def topic_hashtag(topic_id, hashtag, save_type):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM topic_hashtag where topic_id = %s AND hashtag = %s)"
        )
        cur.execute(sql, [int(topic_id), hashtag])
        fetched = cur.fetchone()

        if fetched[0]:
            if not save_type:
                return
            else:
                sql = (
                    "DELETE FROM topic_hashtag "
                    "WHERE topic_id = %s AND hashtag = %s;"
                )
                cur.execute(sql, [int(topic_id), hashtag])
        else:
            if not save_type:
                sql = (
                    "INSERT INTO topic_hashtag "
                    "(topic_id, hashtag) "
                    "VALUES (%s, %s);"
                )
                cur.execute(sql, [int(topic_id), hashtag])
            else:
                return


def get_hashtag_aggregations(topic_id):
    aggregated_hashtags = {}
    length_hashtags = {}
    table_data = {}
    days = Connection.Instance().daily_hastags[str(topic_id)].find()
    today = datetime.today().date()
    last_week = (datetime.today() - timedelta(days=7)).date()
    last_month = (datetime.today() - timedelta(days=30)).date()
    for day in days:
        hashtags = day['hashtag']
        date = day['modified_date'].strftime("%d-%m-%Y")
        for hashtag_tuple in hashtags:
            hashtag = hashtag_tuple['hashtag']
            count = hashtag_tuple['count']
            if hashtag not in table_data:
                table_data[hashtag] = {
                    'today': [],
                    'week': [],
                    'month': []
                }
                if day['modified_date'].date() == today:
                    table_data[hashtag]['today'] = [count]
                    table_data[hashtag]['week'] = [count]
                    table_data[hashtag]['month'] = [count]
                elif day['modified_date'].date() > last_week:
                    table_data[hashtag]['today'] = []
                    table_data[hashtag]['week'] = [count]
                    table_data[hashtag]['month'] = [count]
                elif day['modified_date'].date() > last_month:
                    table_data[hashtag]['today'] = []
                    table_data[hashtag]['week'] = []
                    table_data[hashtag]['month'] = [count]
            else:
                if day['modified_date'].date() == today:
                    counts = table_data[hashtag]['today']
                    counts.append(count)
                    table_data[hashtag]['today'] = counts

                    counts = table_data[hashtag]['week']
                    counts.append(count)
                    table_data[hashtag]['week'] = counts

                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts

                elif day['modified_date'].date() > last_week:
                    counts = table_data[hashtag]['week']
                    counts.append(count)
                    table_data[hashtag]['week'] = counts

                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts
                elif day['modified_date'].date() > last_month:
                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts

            if hashtag not in length_hashtags:
                length_hashtags[hashtag] = count
            else:
                length_hashtags[hashtag] = length_hashtags[hashtag] + count
            if hashtag not in aggregated_hashtags:
                aggregated_hashtags[hashtag] = {}
                aggregated_hashtags[hashtag]['labels'] = [date]
                aggregated_hashtags[hashtag]['data'] = [count]
            else:
                labels = aggregated_hashtags[hashtag]['labels']
                labels.append(date)
                aggregated_hashtags[hashtag]['labels'] = labels

                data = aggregated_hashtags[hashtag]['data']
                data.append(count)
                aggregated_hashtags[hashtag]['data'] = data
    sorted_length = sorted(length_hashtags, key=lambda k: length_hashtags[k], reverse=True)[:50]
    return {
        'sorted': sorted_length,
        'data': aggregated_hashtags,
        'table_data': table_data
    }


def get_mention_aggregations(topic_id):
    aggregated_mentions = {}
    length_mentions = {}
    table_data = {}
    days = Connection.Instance().daily_mentions[str(topic_id)].find()
    today = datetime.today().date()
    last_week = (datetime.today() - timedelta(days=7)).date()
    last_month = (datetime.today() - timedelta(days=30)).date()
    for day in days:
        mentions = day['mention']
        date = day['modified_date'].strftime("%d-%m-%Y")
        for mention_tuple in mentions:
            mention = mention_tuple['mention_username']
            count = mention_tuple['count']

            if mention not in table_data:
                table_data[mention] = {
                    'today': [],
                    'week': [],
                    'month': []
                }
                if day['modified_date'].date() == today:
                    table_data[mention]['today'] = [count]
                    table_data[mention]['week'] = [count]
                    table_data[mention]['month'] = [count]
                elif day['modified_date'].date() > last_week:
                    table_data[mention]['today'] = []
                    table_data[mention]['week'] = [count]
                    table_data[mention]['month'] = [count]
                elif day['modified_date'].date() > last_month:
                    table_data[mention]['today'] = []
                    table_data[mention]['week'] = []
                    table_data[mention]['month'] = [count]
            else:
                if day['modified_date'].date() == today:
                    counts = table_data[mention]['today']
                    counts.append(count)
                    table_data[mention]['today'] = counts

                    counts = table_data[mention]['week']
                    counts.append(count)
                    table_data[mention]['week'] = counts

                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts

                elif day['modified_date'].date() > last_week:
                    counts = table_data[mention]['week']
                    counts.append(count)
                    table_data[mention]['week'] = counts

                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts
                elif day['modified_date'].date() > last_month:
                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts

            if mention not in length_mentions:
                length_mentions[mention] = count
            else:
                length_mentions[mention] = length_mentions[mention] + count
            if mention not in aggregated_mentions:
                aggregated_mentions[mention] = {}
                aggregated_mentions[mention]['labels'] = [date]
                aggregated_mentions[mention]['data'] = [count]
            else:
                labels = aggregated_mentions[mention]['labels']
                labels.append(date)
                aggregated_mentions[mention]['labels'] = labels

                data = aggregated_mentions[mention]['data']
                data.append(count)
                aggregated_mentions[mention]['data'] = data
    sorted_length = sorted(length_mentions, key=lambda k: length_mentions[k], reverse=True)[:50]
    return {
        'sorted': sorted_length,
        'data': aggregated_mentions,
        'table_data': table_data
    }
