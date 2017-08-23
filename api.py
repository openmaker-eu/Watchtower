import json
import time

import logic
from application.Connections import Connection


def getThemes(userid):
    Connection.Instance().cur.execute("select alertid, alertname from alerts where userid = %s", [userid])
    var = Connection.Instance().cur.fetchall()
    themes = [{'alertid': i[0], 'name': i[1]} for i in var]
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)


def getFeeds(themename, date, cursor):
    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    date = determine_date(date)
    themeid = str(logic.getAlertId(themename))
    length = len(list(Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                                   {'$unwind': "$entities.urls"}, \
                                                                   {'$group': {'_id': "$entities.urls.expanded_url",
                                                                               'total': {'$sum': 1}}}])))
    feeds = Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                         {'$unwind': "$entities.urls"}, \
                                                         {'$group': {'_id': "$entities.urls.expanded_url",
                                                                     'total': {'$sum': 1}}}, \
                                                         {'$sort': {'total': -1}}, \
                                                         {'$skip': cursor}, \
                                                         {'$limit': 20}])
    feeds = list(feeds)
    last_feeds = []
    if len(feeds) == 0:
        last_feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next_cursor'] = cursor
    last_feeds = [i['_id'] for i in feeds if i['_id'] != None]
    result['cursor_length'] = length
    result['feeds'] = last_feeds
    return json.dumps(result, indent=4)


def getFeedsGoose(themename, date, cursor):
    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    date = determine_date(date)
    themeid = str(logic.getAlertId(themename))
    length = len(list(Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                                   {'$unwind': "$entities.urls"}, \
                                                                   {'$group': {'_id': "$entities.urls.expanded_url",
                                                                               'total': {'$sum': 1}}}])))
    feeds = Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                         {'$unwind': "$entities.urls"}, \
                                                         {'$group': {'_id': "$entities.urls.expanded_url",
                                                                     'total': {'$sum': 1}}}, \
                                                         {'$sort': {'total': -1}}, \
                                                         {'$skip': cursor}, \
                                                         {'$limit': 20}])
    feeds = list(feeds)
    last_feeds = []
    if len(feeds) == 0:
        last_feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next_cursor'] = cursor
    for link in feeds:
        if link['_id'] != None:
            try:
                g = Goose()
                article = g.extract(url=link['_id'])
                last_feeds.append({'url': link['_id'], 'im': article.top_image.src, 'title': article.title.upper(),
                                   'description': article.meta_description})
            except Exception as e:
                pass
    result['cursor_length'] = length
    result['feeds'] = last_feeds
    return json.dumps(result, indent=4)


def getFeedsSummary(themename, date, cursor):
    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    date = determine_date(date)
    themeid = str(logic.getAlertId(themename))
    length = len(list(Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                                   {'$unwind': "$entities.urls"}, \
                                                                   {'$group': {'_id': "$entities.urls.expanded_url",
                                                                               'total': {'$sum': 1}}}])))
    feeds = Connection.Instance().db[themeid].aggregate([{'$match': {'timestamp_ms': {'$gte': date}}}, \
                                                         {'$unwind': "$entities.urls"}, \
                                                         {'$group': {'_id': "$entities.urls.expanded_url",
                                                                     'total': {'$sum': 1}}}, \
                                                         {'$sort': {'total': -1}}, \
                                                         {'$skip': cursor}, \
                                                         {'$limit': 20}])
    feeds = list(feeds)
    last_feeds = []
    if len(feeds) == 0:
        last_feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next_cursor'] = cursor
    for link in feeds:
        if link['_id'] != None:
            try:
                s = summary.Summary(link['_id'])
                s.extract()
                last_feeds.append(
                    {'url': link['_id'], 'im': str(s.image), 'title': str(s.title), 'description': str(s.description)})
            except Exception as e:
                pass
    result['cursor_length'] = length
    result['feeds'] = last_feeds
    return json.dumps(result, indent=4)


def determine_date(date):
    current_milli_time = int(round(time.time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'month':
        return str(current_milli_time - 30 * one_day)
    return '0'
