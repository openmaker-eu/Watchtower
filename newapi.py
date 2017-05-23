import pymongo
from application.Connections import Connection
import logic
import json

def getThemes(userid):
    Connection.Instance().cur.execute("select alertid, alertname, description from alerts where ispublish = %s", [True])
    var = Connection.Instance().cur.fetchall()
    themes = [{'alertid':i[0], 'name':i[1], 'description': i[2]} for i in var]
    print themes
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)

def getFeeds(themename, themeid, userid, date, cursor):
    try:
        themeid = int(themeid)
    except:
        pass
    if (str(themeid) != "None") and (themename == "None"):
        Connection.Instance().cur.execute("select alertname from alerts where alertid = %s;", [themeid])
        var = Connection.Instance().cur.fetchall()
        themename = var[0][0]
    if themeid != "None" or themename != "None":
        dates=['all', 'yesterday', 'week', 'month']
        result = {}
        if date not in dates:
            result['Error'] = 'invalid date'
            return json.dumps(result, indent=4)
        themeid = str(logic.getAlertIdwithUserId(themename, int(userid)))
        feeds = list(Connection.Instance().newsdB[themeid].find({'name': date}, {date: 1}))
        feeds = list(feeds[0][date][cursor:cursor+20])
        cursor = int(cursor) + 20
        if cursor >= 60:
            cursor = 0
        result['next_cursor'] = cursor
        result['next_cursor_str'] = str(cursor)
        result['feeds'] = feeds
    else:
        result['feeds'] = "theme not found"
    return json.dumps(result, indent=4)

def getInfluencers(themename, themeid):
    try:
        themeid = int(themeid)
    except:
        pass
    if (str(themeid) != "None") and (themename == "None"):
        Connection.Instance().cur.execute("select alertname from alerts where alertid = %s;", [themeid])
        var = Connection.Instance().cur.fetchall()
        themename = var[0][0]
    if themeid != "None" or themename != "None":
        result = {}
        if themename == "arduino":
            themename = "Arduino"
        elif themename == "raspberry pi":
            themename =  "RaspberryPi"
        elif themename == "3d printer":
            themename = "Printer"

        influencers = list(Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0}))
        result['influencers'] = influencers
    else:
        result['influencers'] = "theme not found"
    return json.dumps(result, indent=4)
