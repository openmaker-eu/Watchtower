import pymongo
from application.Connections import Connection
import logic
import json
import dateFilter, crontab3

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

def getNews(themename, themeid, news_ids):
    if news_ids == [""]:
        return json.dumps({'news': "Links not found"}, indent=4)

    if themeid == None and themename == None:
        return json.dumps({'news': "theme not found"}, indent=4)
    elif themeid == None and themename != None:
        try:
            themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'news': "theme not found"}, indent=4)
    elif themeid != None and themename == None:
        try:
            themeid = int(themeid)
            Connection.Instance().cur.execute("select alertname from alerts where alertid = %s;", [themeid])
            var = Connection.Instance().cur.fetchall()
            themename = var[0][0]
        except:
            return json.dumps({'news': "theme not found"}, indent=4)
    else:
        try:
            temp_themeid = str(logic.getAlertId(themename))
        except:
            return json.dumps({'news': "theme not found"}, indent=4)
        if str(temp_themeid) != str(themeid):
            return json.dumps({'news': "theme not found"}, indent=4)

    news_ids = [int(one_id) for one_id in news_ids]

    news = Connection.Instance().newsPoolDB[str(themeid)].find({'link_id': {'$in': news_ids}})

    return json.dumps({'news': links}, indent=4)
