import json

import logic
from application.Connections import Connection


def getThemes(userid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, topic_name, topic_description "
            "FROM topics "
            "WHERE is_publish = %s "
            "ORDER BY topic_id;"
        )
        cur.execute(sql, [True])
        var = cur.fetchall()
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
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [themeid])
            var = cur.fetchall()
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
            if len(feeds) != 0:
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
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [themeid])
            var = cur.fetchall()
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
