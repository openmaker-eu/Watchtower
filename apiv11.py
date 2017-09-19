import json

import logic
from application.Connections import Connection


def getThemes(userid):
    Connection.Instance().cur.execute("select topic_id, topic_name, topic_description from topics where is_publish = %s Order by topic_id", [True])
    var = Connection.Instance().cur.fetchall()
    themes = [{'alertid': i[0], 'name': i[1], 'description': i[2]} for i in var]
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)


def getFeeds(themename, themeid, userid, date, cursor):
    result = {}
    try:
        themeid = int(themeid)
    except:
        pass
    if (str(themeid) != "None") and (themename == "None"):
        Connection.Instance().cur.execute("select topic_name from topics where topic_id = %s;", [themeid])
        var = Connection.Instance().cur.fetchall()
        themename = var[0][0]
    if themeid != "None" or themename != "None":
        dates = ['all', 'yesterday', 'week', 'month']
        if date not in dates:
            result['Error'] = 'invalid date'
            return json.dumps(result, indent=4)

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id "
                "FROM topics "
                "WHERE topic_name = %s"
            )
            cur.execute(sql, [themename])
            themeid = cur.fetchall()[0][0]
            feeds = list(Connection.Instance().filteredNewsPoolDB[str(themeid)].find({"name": date}, {date: 1}))
            print(feeds, themeid)
            feeds = list(feeds[0][date][cursor:cursor + 20])
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
        Connection.Instance().cur.execute("select topic_name from topics where topic_id = %s;", [themeid])
        var = Connection.Instance().cur.fetchall()
        themename = var[0][0]
    if themeid != "None" or themename != "None":
        result = {}
        if themename == "arduino":
            themename = "Arduino"
        elif themename == "raspberry pi":
            themename = "RaspberryPi"
        elif themename == "3d printer":
            themename = "Printer"

        influencers = list(
            Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id": 0, "type": 0}))
        result['influencers'] = influencers
    else:
        result['influencers'] = "theme not found"
    return json.dumps(result, indent=4)
