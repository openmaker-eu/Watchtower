import pymongo
from application.Connections import Connection
import logic
import json

def getThemes(userid):
    Connection.Instance().cur.execute("select alertid, alertname from alerts where userid = %s", [userid])
    var = Connection.Instance().cur.fetchall()
    themes = [{'alertid':i[0], 'name':i[1]} for i in var]
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)

def getFeeds(themename, userid, date, cursor):
    dates=['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    themeid = str(logic.getAlertIdwithUserId(themename, int(userid)))
    feeds = list(Connection.Instance().newsdB[themeid].find({'name': date}, {date: 1}))
    feeds = list(feeds[0][date][cursor:cursor+20])
    if len(feeds) == 0:
        feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= 60:
            cursor = 60
        result['next_cursor'] = cursor
    result['cursor_length'] = 60
    result['feeds'] = feeds
    return json.dumps(result, indent=4)

def getInfluencers(themename, cursors):
    result = {}
    if themename == "arduino":
        themename = "Arduino"
    elif themename == "raspberry pi":
        themename =  "RaspberryPi"
    elif themename == "3d printer":
        themename = "Printer"

    influencers = list(Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0}))
    if influencers == []:
        if cursor > 20:
            result['influencers'] = "cursor not found"
        else:
            result['influencers'] = "themename not found"
    else:
        cursor = int(cursor) + 20
        if cursor >= 20:
            cursor = 20
        result['next_cursor'] = cursor
        result['influencers'] = influencers
    result['cursor_length'] = 20
    return result
