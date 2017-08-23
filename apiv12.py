import pymongo
from application.Connections import Connection
import logic
import json
import dateFilter, crontab3
from bson import json_util
import bson.objectid
from datetime import datetime
import time, re

def getEvents(topic_id, filterField, cursor):

    now = time.time()
    cursor = int(cursor)
    ret = None
    if filterField == 'interested':
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            { '$match' : { 'end_time' : { '$gte' : now } } },
            { '$project' : { '_id' : 0 } },
            { '$sort' : { 'interested' : -1} },
            { '$skip' : int(cursor) },
            { '$limit' : 10 }
        ])
    elif filterField == 'date':
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            { '$match' : { 'end_time' : { '$gte' : now } } },
            { '$project' : { '_id' : 0 } },
            { '$sort' : { 'start_time' : -1} },
            { '$skip' : int(cursor) },
            { '$limit' : 10 }
        ])
    ret = list(ret)
    temp = {'events': ret}
    return temp

def getConversations(topic_id, timeFilter, paging):
    curser = Connection.Instance().conversations[str(topic_id)].find({"time_filter" : timeFilter}, {"posts": { "$slice": [ int(paging), 10 ] }, "_id":0})
    for document in curser:
        docs = []
        for submission in document["posts"]:
            if not submission["numberOfComments"]:
                continue
            comments = []
            for comment in submission["comments"]:
                comment["relative_indent"] = 0
                if submission['source'] == 'reddit':
                    comment["created_time"] = datetime.fromtimestamp(int(comment["created_time"])).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    comment["created_time"] = comment["created_time"][:10]+" "+comment["created_time"][11:18]
                comments.append(comment)
            temp = {"title":submission["title"],"source":submission["source"],"comments":comments,"url":submission["url"],"commentNumber":submission["numberOfComments"]}
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


def my_handler(x):
    if isinstance(x, datetime):
        return x.strftime("%d-%m-%Y")
    elif isinstance(x, bson.objectid.ObjectId):
        return str(x)
    else:
        raise TypeError(x)

def getTopics():
    Connection.Instance().cur.execute("select alertid, alertname, description from alerts where ispublish = %s", [True])
    var = Connection.Instance().cur.fetchall()
    topics = [{'topic_id':i[0], 'topic_name':i[1], 'description': i[2]} for i in var]
    result = {}
    result['topics'] = topics
    return json.dumps(result, indent=4)

def getNewsFeeds(date, cursor, forbidden_domain, topics):
    if topics == [""]:
        return json.dumps({}, indent=4)

    dates=['yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)

    #feeds = list(Connection.Instance().filteredNewsPoolDB[themeid].find({'name': date}, {date: 1}))
    #feeds = list(feeds[0][date][cursor:cursor+20])

    date=crontab3.determine_date(date)

    news = []
    for topic_id in topics:
        if len(news) >= cursor+20:
            break
        news = news + dateFilter.getDateList(topic_id, int(date), forbidden_domain)

    news = news[cursor:cursor+20]

    cursor = int(cursor) + 20
    if cursor >= 60:
        cursor = 0
    result['next_cursor'] = cursor
    result['next_cursor_str'] = str(cursor)
    result['news'] = news

    return json.dumps(result, indent=4)

def getAudiences(topic_id):
    if topic_id == None:
        return json.dumps({}, indent=4)

    audiences = list(Connection.Instance().infDB[str(topic_id)].find({}, {'_id':0, 'screen_name': 1, 'location':1, 'name':1, 'profile_image_url':1, 'lang':1, 'description':1, 'time_zone':1}).sort([('rank', pymongo.ASCENDING)]))

    return json.dumps({'audiences' : audiences}, indent=4)

def getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor, since, until, domains, topics):
    cursor = int(cursor)
    if news_ids == [""] and keywords == [""] and since == "" and until == "" and\
     languages == [""] and cities == [""] and countries == [""] and user_location == [""]\
     and user_language == [""] and domains == [""]:
        return json.dumps({'news': [], 'next_cursor': 0, 'next_cursor_str': "0"}, indent=4)

    aggregate_dictionary = []
    find_dictionary = {}
    date_dictionary = {}
    language_dictionary = None
    city_dictionary = None
    country_dictionary = None
    user_location_dictionary = None
    user_language_dictionary = None
    news_ids_in_dictionary = None
    keywords_in_dictionary = None
    domains_in_dictionary = None
    since_in_dictionary = None
    until_in_dictionary = None

    if news_ids != [""]:
        news_ids_in_dictionary = [int(one_id) for one_id in news_ids]
        find_dictionary['link_id'] = {'$in': news_ids_in_dictionary}

    if keywords != [""]:
        keywords_in_dictionary = [re.compile(key, re.IGNORECASE) for key in keywords]
        find_dictionary['$or'] = [{'title': {'$in': keywords_in_dictionary}}, {'description': {'$in': keywords_in_dictionary}}]

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
            date_dictionary['$gte'] =  since_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"}, indent=4)

    if until != "":
        try:
            until_in_dictionary = datetime.strptime(until, "%d-%m-%Y")
            date_dictionary['$lte'] =  until_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"}, indent=4)

    if date_dictionary != {}:
        find_dictionary['published_at'] = date_dictionary

    aggregate_dictionary.append({'$match': find_dictionary})
    if user_language == [""] and user_location == [""]:
        aggregate_dictionary.append({'$project': {'mentions':0}})
    aggregate_dictionary.append({'$project': {'_id': 0, 'bookmark':0, 'bookmark_date':0, 'location': 0}})

    aggregate_dictionary.append({'$sort': {'link_id' : -1}})

    print(aggregate_dictionary)

    topics_filter = []
    if topics != [""]:
        topics_filter = [int(one_id) for one_id in topics]

    news = []
    for alertid in Connection.Instance().newsPoolDB.collection_names():
        if len(news) >= cursor+20:
            break
        if topics_filter == []:
            news = news + list(Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary))
        else:
            if int(alertid) in topics_filter:
                news = news + list(Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary))

    next_cursor = cursor + 20
    if len(news) < cursor+20:
        next_cursor = 0

    result = {
        'next_cursor': next_cursor,
        'next_cursor_str': str(next_cursor),
        'news': news[cursor:cursor+20]
    }

    return json.dumps(result, indent=4, default=my_handler)

def getHastags(topic_id, date):
    if topic_id == None:
        return json.dumps({}, indent=4)

    hashtags = list(Connection.Instance().hashtags[str(topic_id)].find({'name': date}, {'_id': 0, 'modified_date': 0}))[0][date]

    return json.dumps({'hashtags': hashtags}, indent=4)
