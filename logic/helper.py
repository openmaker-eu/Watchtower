__author__ = ['Enis Simsar']

import json
import re
from urllib.parse import urlparse

import praw
import psycopg2
import requests
import facebook
from decouple import config

from application.Connections import Connection
from crontab_module.crons import facebook_reddit_crontab
from datetime import datetime


def get_relevant_locations():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM relevant_locations;"
        )
        cur.execute(sql, [])
        locations = cur.fetchall()
        return [{'location_name': i[0], 'location_code': i[1]} for i in locations]


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


def get_next_tweet_sequence():
    cursor = Connection.Instance().tweetsDB["counters"].find_and_modify(
        query={'_id': "tweet_id"},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return cursor['seq']


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
    graph = facebook.GraphAPI(access_token=my_token, version="2.12")
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
