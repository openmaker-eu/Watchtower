__author__ = ['Enis Simsar']

import pymongo

from application.utils import general


from application.Connections import Connection
from logic.helper import scrape_url, get_next_tweet_sequence


def get_tweet(topic_id, tweet_id):
    if int(tweet_id) != -1:
        return Connection.Instance().tweetsDB[str(topic_id)].find_one({'tweet_id': int(tweet_id)})
    return []


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

