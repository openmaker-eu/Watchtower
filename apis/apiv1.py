import json
import sys

sys.path.append('../')

from application.Connections import Connection


def getThemes():
    names = Connection.Instance().feedDB.collection_names()
    result = {}
    themes = [{'name': name} for name in names]
    result['themes'] = themes
    return json.dumps(result, indent=4)


def getInfluencers(themename, cursor):
    length = len(
        list(Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id": 0, "type": 0})))
    if cursor is None:
        influencers = Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"},
                                                                       {"_id": 0, "type": 0}).skip(0).limit(20)
        cursor = 0
    else:
        influencers = Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"},
                                                                       {"_id": 0, "type": 0}).skip(int(cursor)).limit(
            20)
    result = {}
    influencers = list(influencers)
    if len(influencers) == 0:
        influencers.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next cursor'] = cursor
    result['cursor length'] = length
    result['influencers'] = influencers
    return json.dumps(result, indent=4)


def getFeeds(themename, cursor=0):
    length = len(list(Connection.Instance().feedDB[str(themename)].find({}, {"_id": 0})))
    if cursor is None:
        feeds = Connection.Instance().feedDB[str(themename)].find({}, {"_id": 0}).skip(0).limit(20)
        cursor = 0
    else:
        feeds = Connection.Instance().feedDB[str(themename)].find({}, {"_id": 0}).skip(int(cursor)).limit(20)
    result = {}
    feeds = list(feeds)
    if len(feeds) == 0:
        feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next cursor'] = cursor
    result['cursor length'] = length
    result['feeds'] = feeds
    return json.dumps(result, indent=4)
