# Author: Kemal Berk Kocabagli

import json
import re
import logic
import time
from application.Connections import Connection
import location_regex # to get regular expressions for locations

def getLocalInfluencers(topic_id, location, cursor):
    cursor = int(cursor)
    try:
        topic_id = int(topic_id)
    except:
        pass
    if (str(topic_id) != "None"):
        Connection.Instance().cur.execute("select topic_name from topics where topic_id = %s;", [topic_id])
        var = Connection.Instance().cur.fetchall()
        topic_name = var[0][0]
        result = {}
        # error handling needed for location
        location = location.lower()

        local_influencers = list(
        Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)].find({},
         {'_id': False,
         'name':1,
         'screen_name':1,
         'location':1,
         'description':1,
         'time-zone':1,
         'lang':1,
         'profile_image_url_https':1
         })[cursor:cursor+10]
        )

        result['topic'] = topic_name
        result['location'] = location
        cursor = int(cursor) + 10
        if cursor >= 100 or len(local_influencers) == 0:
            cursor = 0
        result['next_cursor'] = cursor
        result['local_influencers'] = local_influencers
    else:
        result['local_influencers'] = "topic not found"
    return json.dumps(result, indent=4)

def getAudienceSample(topic_id, location, cursor):
    cursor = int(cursor)
    try:
        topic_id = int(topic_id)
    except:
        pass
    if (str(topic_id) != "None"):
        Connection.Instance().cur.execute("select topic_name from topics where topic_id = %s;", [topic_id])
        var = Connection.Instance().cur.fetchall()
        topic_name = var[0][0]

        result = {}

        # error handling needed for location
        print("Location: " + str(location))
        location = location.lower()

        audience_sample = list(
        Connection.Instance().audience_samples_DB[str(location)+"_"+str(topic_id)].find({},
        {'_id': False,
        'name':1,
        'screen_name':1,
        'location':1,
        'description':1,
        'time-zone':1,
        'lang':1,
        'profile_image_url_https':1
        })[cursor:cursor+10]
        )

        result['topic'] = topic_name
        result['location'] = location
        cursor = int(cursor) + 10
        if cursor >= 100 or len(audience_sample) == 0:
            cursor = 0
        result['next_cursor'] = cursor
        result['audience_sample'] = audience_sample

    else:
        result['audience_sample'] = "topic not found"
    return json.dumps(result, indent=4)

def getEvents(topic_id, sortedBy, date, location, cursor):
    now = time.time()
    cursor = int(cursor)
    result = {}
    events = []

    Connection.Instance().cur.execute("select topic_name from topics where topic_id = %s;", [topic_id])
    var = Connection.Instance().cur.fetchall()
    topic_name = var[0][0]

    match = {'end_time': {'$gte': now}}
    sort = {}

    if location !="":
        match['place']= location_regex.getLocationRegex(location)

    if sortedBy == 'interested':
        sort['interested']=-1
    elif sortedBy == 'date' or sortedBy=='':
        sort['start_time']=-1
    else:
        return {'error': "please enter a valid sortedBy value."}

    events = Connection.Instance().events[str(topic_id)].aggregate([
        {'$match': match},
        {'$project': {'_id': 0}},
        {'$sort': sort},
        {'$skip': int(cursor)},
        {'$limit': 10}
    ])

    events = list(events)
    cursor = int(cursor) + 10
    if cursor >= 100 or len(events) == 0:
        cursor = 0
    result['topic'] = topic_name
    result['next_cursor'] = cursor
    result['events']= events
    return result
