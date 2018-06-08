__author__ = ['Enis Simsar']

import json

from application.Connections import Connection
from application.utils import twitter_search_sample_tweets


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
