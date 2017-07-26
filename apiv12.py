import pymongo
from application.Connections import Connection
import logic
import json
import dateFilter, crontab3
import re, datetime
from bson import json_util
import bson.objectid

def my_handler(x):
    if isinstance(x, datetime.datetime):
        return x.strftime("%H:%M:%S %d-%m-%Y")
    elif isinstance(x, bson.objectid.ObjectId):
        return str(x)
    else:
        raise TypeError(x)

def getThemes(userid):
    Connection.Instance().cur.execute("select alertid, alertname, description from alerts where ispublish = %s", [True])
    var = Connection.Instance().cur.fetchall()
    themes = [{'themeid':i[0], 'themename':i[1], 'description': i[2]} for i in var]
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)

def getFeeds(themename, themeid, date, cursor, forbidden_domain):
    if themeid == None and themename == None:
        return json.dumps({'feeds': "theme not found"}, indent=4)
    elif themeid == None and themename != None:
        try:
            themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'feeds': "theme not found"}, indent=4)
    elif themeid != None and themename == None:
        try:
            themeid = int(themeid)
            Connection.Instance().cur.execute("select alertname from alerts where alertid = %s;", [themeid])
            var = Connection.Instance().cur.fetchall()
            themename = var[0][0]
        except:
            return json.dumps({'feeds': "theme not found"}, indent=4)
    else:
        try:
            temp_themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'feeds': "theme not found"}, indent=4)
        if str(temp_themeid) != str(themeid):
            return json.dumps({'feeds': "theme not found"}, indent=4)

    dates=['yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)

    #feeds = list(Connection.Instance().filteredNewsPoolDB[themeid].find({'name': date}, {date: 1}))
    #feeds = list(feeds[0][date][cursor:cursor+20])

    date=crontab3.determine_date(date)
    feeds = dateFilter.getDateList(themeid, int(date), forbidden_domain)
    feeds = feeds[cursor:cursor+20]

    cursor = int(cursor) + 20
    if cursor >= 60:
        cursor = 0
    result['next_cursor'] = cursor
    result['next_cursor_str'] = str(cursor)
    result['feeds'] = feeds

    return json.dumps(result, indent=4)

def getInfluencers(themename, themeid):
    if themeid == None and themename == None:
        return json.dumps({'influencers': "theme not found"}, indent=4)
    elif themeid == None and themename != None:
        try:
            themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'influencers': "theme not found"}, indent=4)
    elif themeid != None and themename == None:
        try:
            themeid = int(themeid)
            Connection.Instance().cur.execute("select alertname from alerts where alertid = %s;", [themeid])
            var = Connection.Instance().cur.fetchall()
            themename = var[0][0]
        except:
            return json.dumps({'influencers': "theme not found"}, indent=4)
    else:
        try:
            temp_themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'influencers': "theme not found"}, indent=4)
        if str(temp_themeid) != str(themeid):
            return json.dumps({'influencers': "theme not found"}, indent=4)

    result = {}
    if themename == "arduino":
        themename = "Arduino"
    elif themename == "raspberry pi":
        themename =  "RaspberryPi"
    elif themename == "3d printer":
        themename = "Printer"

    influencers = list(Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0}))
    result['influencers'] = influencers

    return json.dumps(result, indent=4)

def getNews(news_ids, keywords, cursor, since, until):
    cursor = int(cursor)
    if news_ids == [""] and keywords == [""] and since == "" and until == "":
        return json.dumps({'news': "Empty news id list", 'next_cursor': 0, 'next_cursor_str': "0"}, indent=4)

    find_dictionary = {}
    date_dictionary = {}
    news_ids_in_dictionary = None
    keywords_in_dictionary = None
    since_in_dictionary = None
    until_in_dictionary = None

    if news_ids != [""]:
        news_ids_in_dictionary = [int(one_id) for one_id in news_ids]
        find_dictionary['link_id'] = {'$in': news_ids_in_dictionary}

    if keywords != [""]:
        keywords_in_dictionary = [re.compile(key, re.IGNORECASE) for key in keywords]
        find_dictionary['$or'] = [{'title': {'$in': keywords_in_dictionary}}, {'description': {'$in': keywords_in_dictionary}}]

    if since != "":
        try:
            since_in_dictionary = datetime.datetime.strptime(since, "%d-%m-%Y")
            date_dictionary['$gte'] =  since_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"}, indent=4)

    if until != "":
        try:
            until_in_dictionary = datetime.datetime.strptime(until, "%d-%m-%Y")
            date_dictionary['$lte'] =  until_in_dictionary
        except ValueError:
            return json.dumps({'error': "please, enter a valid since day. DAY-MONTH-YEAR"}, indent=4)

    if date_dictionary != {}:
        find_dictionary['published_at'] = date_dictionary

    news = []
    for alertid in Connection.Instance().newsPoolDB.collection_names():
        if len(news) >= cursor+20:
            break
        news = news + list(Connection.Instance().newsPoolDB[str(alertid)].find(find_dictionary, {"_id":0, 'mentions': 0, 'bookmark':0}))

    next_cursor = cursor + 20
    if len(news) < cursor+20:
        next_cursor = 0

    result = {
        'next_cursor': next_cursor,
        'next_cursor_str': str(next_cursor),
        'news': news[cursor:cursor+20]
    }
    return json.dumps(result, indent=4, default=my_handler)
