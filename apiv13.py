import json
import re
import logic
import time
from application.Connections import Connection

def getLocalInfluencers(topic_id, location):
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
            Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)].find({}, {'_id': False}))
        result['topic'] = topic_name
        result['location'] = location
        result['local_influencers'] = local_influencers
    else:
        result['local_influencers'] = "topic not found"
    return json.dumps(result, indent=4)

def getAudienceSample(topic_id, location):
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
            Connection.Instance().audience_samples_DB[str(location)+"_"+str(topic_id)].find({}, {'_id': False}))
        result['topic'] = topic_name
        result['location'] = location
        result['audience_sample'] = audience_sample
    else:
        result['audience_sample'] = "topic not found"
    return json.dumps(result, indent=4)

def getEvents(topic_id, filterField, place, cursor):
    now = time.time()
    cursor = int(cursor)
    result = {}
    events = []
    if filterField == 'interested':
        events = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'end_time': {'$gte': now}}},
            {'$project': {'_id': 0}},
            {'$sort': {'interested': -1}},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])
    elif filterField == 'date':
        events = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'end_time': {'$gte': now}}},
            {'$project': {'_id': 0}},
            {'$sort': {'start_time': -1}},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])
    '''
    elif filterField == 'place':
        events = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'end_time': {'$gte': now}}},
            {'$project': {'_id': 0}},
            {'$sort': {'start_time': -1}},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])
    '''
    events = list(events)
    cursor = int(cursor) + 10
    if cursor >= 100 or len(events) == 0:
        cursor = 0

    result['next_cursor'] = cursor
    result['events']= events
    return result
