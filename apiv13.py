# Author: Kemal Berk Kocabagli

import json
import re
import logic
import time
from application.Connections import Connection
import location_regex # to get regular expressions for locations
import csv # for sort by location
import pprint
def getLocalInfluencers(topic_id, location, cursor):
    cursor = int(cursor)
    result = {}
    try:
        topic_id = int(topic_id)
    except:
        result['local_influencers'] = "topic not found"
        return json.dumps(result, indent=4)
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]

            # error handling needed for location
            location = location.lower()

            local_influencers = list(
            Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)].find({},
             {'_id': False,
             'name':1,
             'screen_name':1,
             'description':1,
             'location':1,
             'time-zone':1,
             'lang':1,
             'profile_image_url_https':1
             })[cursor:cursor+10]
            )

            result['topic'] = topic_name
            result['location'] = location
            cursor = int(cursor) + 10
            if cursor >= 20 or len(local_influencers) < 10:
                cursor = 0
            result['next_cursor'] = cursor
            result['local_influencers'] = local_influencers
    else:
        result['local_influencers'] = "topic not found"
    return json.dumps(result, indent=4)

def getAudienceSample(topic_id, location, cursor):
    cursor = int(cursor)
    result = {}
    try:
        topic_id = int(topic_id)
    except:
        result['audience_sample'] = "topic not found"
        return json.dumps(result, indent=4)
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]

            # error handling needed for location
            print("Location: " + str(location))
            location = location.lower()

            audience_sample = list(
            Connection.Instance().audience_samples_DB[str(location)+"_"+str(topic_id)].find({},
            {'_id': False,
            'name':1,
            'screen_name':1,
            'description':1,
            'location':1,
            'time-zone':1,
            'lang':1,
            'profile_image_url_https':1
            })[cursor:cursor+10]
            )

            result['topic'] = topic_name
            result['location'] = location
            cursor = int(cursor) + 10
            if cursor >= 100 or len(audience_sample) < 10:
                cursor = 0
            result['next_cursor'] = cursor
            result['audience_sample'] = audience_sample

    else:
        result['audience_sample'] = "topic not found"
    return json.dumps(result, indent=4)

def getEvents(topic_id, sortedBy, location, cursor):
    now = time.time()
    cursor = int(cursor)
    result = {}
    events = []
    try:
        topic_id = int(topic_id)
    except:
        result['event'] = "topic not found"
        return json.dumps(result, indent=4)
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_name "
            "FROM topics "
            "WHERE topic_id = %s;"
        )
        cur.execute(sql, [topic_id])
        var = cur.fetchall()
        topic_name = var[0][0]

        events = [] # all events to be returned
        match = {'end_time': {'$gte': now}}
        sort = {}
        result['topic'] = topic_name


        # SORT CRITERIA
        if sortedBy == 'interested':
            sort['interested']=-1
        elif sortedBy == 'date' or sortedBy=='':
            sort['start_time']=1
        else:
            return {'error': "please enter a valid sortedBy value."}


        if location !="":
            EVENT_LIMIT = 100
            COUNTRY_LIMIT=50
            cdl = []
            with open('rank_countries.csv', 'r') as f:
              reader = csv.reader(f)
              country_distance_lists = list(reader)
              for i in range(len(country_distance_lists)):
                  if country_distance_lists[i][0] == location:
                      cdl = country_distance_lists[i]
              print("Found cdl!")
              count = 0
              for country in cdl:
                  print("Checking db for country (#" + str(count) + "): " + str(country))
                  match['place']= location_regex.getLocationRegex(country)
                  events += list(Connection.Instance().events[str(topic_id)].aggregate([
                      {'$match': match},
                      {'$project': {'_id': 0,
                          "updated_time": 1,
                          "cover": 1,
                          "end_time": 1,
                          "description":1,
                          "id": 1,
                          "name": 1,
                          "place": 1,
                          "start_time": 1,
                          "link": 1,
                          "interested": 1,
                          "coming":1
                      }},
                      {'$sort': sort}
                      #{'$skip': int(cursor)},
                      #{'$limit': 10}
                  ]))
                  count+=1
                  print("length:" + str(len(events)))
                  if len(events) > min(cursor+10,EVENT_LIMIT):
                      break
                  if (count > COUNTRY_LIMIT):
                      break

            pprint.pprint([e['place'] for e in events])
            display_events= events[cursor:cursor+10]
            cursor = int(cursor) + 10
            if cursor >= 100 or len(events) <cursor+10:
                cursor = 0
            result['next_cursor'] = cursor
            result['events'] = display_events

        else:
            events = list(Connection.Instance().events[str(topic_id)].aggregate([
                {'$match': match},
                {'$project': {'_id': 0,
                    "updated_time": 1,
                    "cover": 1,
                    "end_time": 1,
                    "description":1,
                    "id": 1,
                    "name": 1,
                    "place": 1,
                    "start_time": 1,
                    "link": 1,
                    "interested": 1,
                    "coming":1
                }},
                {'$sort': sort},
                {'$skip': int(cursor)},
                {'$limit': 10}
            ]))
            cursor = int(cursor) + 10
            if cursor >= 100 or len(events) <10:
                cursor = 0
            result['next_cursor'] = cursor
            result['events']= events

        return result
