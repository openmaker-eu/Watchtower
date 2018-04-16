import json
import operator
import re
import sys
import time
from datetime import datetime

import pymongo

sys.path.append('../')

from application.Connections import Connection
from application.utils import general


def getTopics(keywords):
    if keywords != [""]:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id "
                "FROM topics "
                "WHERE is_publish = %s"
            )
            cur.execute(sql, [True])
            var = cur.fetchall()
            published_topics = []
            if var is not None:
                published_topics = [i[0] for i in var]
            print(published_topics)
            keywords_in_dictionary = [re.compile(key, re.IGNORECASE) for key in keywords]
            topic_list = {}
            for topic_id in Connection.Instance().hashtags.collection_names():
                if topic_id != "counters" and int(topic_id) in published_topics:
                    try:
                        count = list(Connection.Instance().hashtags[str(topic_id)].aggregate([
                            {'$unwind': "$month"},
                            {'$project': {
                                'hashtag': '$month.hashtag', 'count': '$month.count'
                            }
                            },
                            {
                                '$match': {
                                    'hashtag': {'$in': keywords_in_dictionary}
                                }
                            },
                            {
                                '$group':
                                    {
                                        '_id': {},
                                        'count': {'$sum': "$count"}
                                    }
                            }]))[0]['count']
                        topic_list[str(topic_id)] = count
                    except:
                        pass
            topics = topic_list.keys()
            topics = [int(topic_id) for topic_id in topics]
            print(sorted(topic_list.items(), key=operator.itemgetter(1), reverse=True))
            if len(topics) == 0:
                topics = [-1]
            sql = (
                "SELECT topic_id, topic_name, topic_description "
                "FROM topics "
                "WHERE is_publish = %s and topic_id IN %s"
            )
            cur.execute(sql, [True, tuple(topics)])
            var = cur.fetchall()
            topics = {str(i[0]): {'topic_name': i[1], 'description': i[2]} for i in var}
            result = []
            for topic in sorted(topic_list.items(), key=operator.itemgetter(1), reverse=True):
                if str(topic[0]) in topics:
                    temp = topics[str(topic[0])]
                    temp['topic_id'] = int(topic[0])
                    result.append(temp)
            return json.dumps({'topics': result})
    else:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id, topic_name, topic_description "
                "FROM topics "
                "WHERE is_publish = %s "
                "ORDER BY topic_id"
            )
            cur.execute(sql, [True])
            var = cur.fetchall()
            topics = [{'topic_id': i[0], 'topic_name': i[1], 'description': i[2]} for i in var]
            return json.dumps({'topics': topics})


def getNewsFeeds(date, cursor, forbidden_domain, topics):
    if topics == [""]:
        return json.dumps({})

    dates = ['yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result)

    # feeds = list(Connection.Instance().filteredNewsPoolDB[themeid].find({'name': date}, {date: 1}))
    # feeds = list(feeds[0][date][cursor:cursor+20])

    # date = general_utils.determine_date(date)

    news = []
    for topic_id in topics:
        # if len(news) >= cursor + 20:
        #    break
        feeds = list(Connection.Instance().filteredNewsPoolDB[str(topic_id)].find({'name': date}, {date: 1}))
        if len(feeds) > 0:
            news = news + feeds[0][date]

    news = news[cursor:cursor + 20]

    cursor = int(cursor) + 20
    if cursor >= 60:
        cursor = 0
    result['next_cursor'] = cursor
    result['next_cursor_str'] = str(cursor)
    result['news'] = news

    return json.dumps(result)


def getAudiences(topic_id):
    if topic_id is None:
        return json.dumps({})

    audiences = list(Connection.Instance().infDB[str(topic_id)].find({}, {'_id': 0, 'screen_name': 1, 'location': 1,
                                                                          'name': 1, 'profile_image_url': 1, 'lang': 1,
                                                                          'summary': 1, 'full_text': 1,
                                                                          'time_zone': 1}).sort(
        [('rank', pymongo.ASCENDING)]))

    return json.dumps({'audiences': audiences})


def getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor, since, until,
            domains, topics):
    cursor = int(cursor)
    if news_ids == [""] and keywords == [""] and since == "" and until == "" and \
            languages == [""] and cities == [""] and countries == [""] and user_location == [""] \
            and user_language == [""] and domains == [""]:
        return json.dumps({'news': [], 'next_cursor': 0, 'next_cursor_str': "0"})

    aggregate_dictionary = []
    find_dictionary = {}
    date_dictionary = {}

    if news_ids != [""]:
        news_ids_in_dictionary = [int(one_id) for one_id in news_ids]
        find_dictionary['link_id'] = {'$in': news_ids_in_dictionary}

    if keywords != [""]:
        keywords_in_dictionary = [re.compile(key, re.IGNORECASE) for key in keywords]
        find_dictionary['$or'] = [{'title': {'$in': keywords_in_dictionary}},
                                  {'summary': {'$in': keywords_in_dictionary}},
                                  {'full_text': {'$in': keywords_in_dictionary}}]

    if domains != [""]:
        domains_in_dictionary = [re.compile(key, re.IGNORECASE) for key in domains]
        find_dictionary['domain'] = {'$nin': domains_in_dictionary}

    if languages != [""]:
        language_dictionary = [lang for lang in languages]
        find_dictionary['language'] = {'$in': language_dictionary}

    if cities != [""]:
        city_dictionary = [re.compile(city, re.IGNORECASE) for city in cities]
        find_dictionary['location.cities'] = {'$in': city_dictionary}
        aggregate_dictionary.append({'$unwind': '$location.cities'})

    if countries != [""]:
        country_dictionary = [re.compile(country, re.IGNORECASE) for country in countries]
        find_dictionary['location.countries'] = {'$in': country_dictionary}
        aggregate_dictionary.append({'$unwind': '$location.countries'})

    if user_location != [""]:
        user_location_dictionary = [re.compile(city, re.IGNORECASE) for city in user_location]
        find_dictionary['mentions.location'] = {'$in': user_location_dictionary}
        aggregate_dictionary.append({'$unwind': '$mentions'})

    if user_language != [""]:
        user_language_dictionary = [re.compile(country, re.IGNORECASE) for country in user_language]
        find_dictionary['mentions.language'] = {'$in': user_language_dictionary}
        aggregate_dictionary.append({'$unwind': '$mentions'})

    if since != "":
        try:
            since_in_dictionary = datetime.strptime(since, "%d-%m-%Y")
            date_dictionary['$gte'] = since_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"})

    if until != "":
        try:
            until_in_dictionary = datetime.strptime(until, "%d-%m-%Y")
            date_dictionary['$lte'] = until_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"})

    if date_dictionary != {}:
        find_dictionary['published_at'] = date_dictionary

    aggregate_dictionary.append({'$match': find_dictionary})
    if user_language == [""] and user_location == [""]:
        aggregate_dictionary.append({'$project': {'mentions': 0}})
    aggregate_dictionary.append({'$project': {'_id': 0, 'bookmark': 0, 'bookmark_date': 0, 'location': 0}})

    aggregate_dictionary.append({'$sort': {'link_id': -1}})

    print(aggregate_dictionary)

    topics_filter = []
    if topics != [""]:
        topics_filter = [int(one_id) for one_id in topics]

    news = []
    for alertid in Connection.Instance().newsPoolDB.collection_names():
        if alertid != "counters":
            if len(news) >= cursor + 20:
                break
            if topics_filter == []:
                news = news + list(
                    Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary, allowDiskUse=True))
            else:
                if int(alertid) in topics_filter:
                    news = news + list(Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary,
                                                                                                allowDiskUse=True))

    next_cursor = cursor + 20
    if len(news) < cursor + 20:
        next_cursor = 0

    result = {
        'next_cursor': next_cursor,
        'next_cursor_str': str(next_cursor),
        'news': news[cursor:cursor + 20]
    }

    return json.dumps(result, default=general.date_formatter)


def getHastags(topic_id, date):
    if topic_id is None:
        return json.dumps({})

    hashtag_list = list(
        Connection.Instance().hashtags[str(topic_id)].find({'name': date}, {'_id': 0, 'modified_date': 0}))

    hashtags = []

    if len(hashtag_list) > 0:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT ARRAY_AGG(hashtag) FROM topic_hashtag WHERE topic_id = %s ;"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchone()
            tags = var[0] if var[0] is not None else []
            hashtags = [item for item in hashtag_list[0][date] if item['hashtag'] not in tags]

    return json.dumps({'hashtags': hashtags})


def getEvents(topic_id, filterField, cursor):
    now = time.time()
    cursor = int(cursor)
    print(now)
    ret = []
    if filterField == 'interested':
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'end_time': {'$gte': now}}},
            {'$project': {'_id': 0}},
            {'$sort': {'interested': -1}},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])
    elif filterField == 'date':
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'end_time': {'$gte': now}}},
            {'$project': {'_id': 0}},
            {'$sort': {'start_time': 1}},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])
    ret = list(ret)
    temp = {'events': ret}
    return temp


def getConversations(topic_id, timeFilter, paging):
    curser = Connection.Instance().conversations[str(topic_id)].find({"time_filter": timeFilter},
                                                                     {"posts": {"$slice": [int(paging), 10]}, "_id": 0})

    for document in curser:
        docs = []
        for submission in document["posts"]:
            if not submission["numberOfComments"]:
                continue
            comments = []
            for comment in submission["comments"]:
                comment["relative_indent"] = 0
                if submission['source'] == 'reddit':
                    comment["created_time"] = comment["created_time"]
                else:
                    comment["created_time"] = comment["created_time"][:10] + " " + comment["created_time"][11:18]
                comments.append(comment)

            temp = {"title": submission["title"], "source": submission["source"], "comments": comments,
                    "url": submission["url"], "commentNumber": submission["numberOfComments"],
                    'subreddit': submission['subreddit'], 'created_time': submission['created_time']}
            if "post_text" in submission:
                temp["post_text"] = submission["post_text"]
            else:
                temp["post_text"] = ""
            docs.append(temp)
        prev = 0
        for values in docs:
            for current in values["comments"]:
                current["relative_indent"] = current["indent_number"] - prev
                prev = current["indent_number"]
        return docs
