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
    '''
    returns maximum 20 local influencers for the given topic and location; 10 in each page.
    if next_cursor = 0, you are on the last page.
    '''
    result = {}
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )

            try:
                cur.execute(sql, [topic_id])
                var = cur.fetchall()
                topic_name = var[0][0]
            except:
                result['error'] = "Topic does not exist."
                return json.dumps(result, indent=4)

            # error handling needed for location
            location = location.lower()

            collection = Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)]

            if location == "global":
                collection = Connection.Instance().influencerDB[str(topic_id)]

            local_influencers = list(
                collection.find({},
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

            cursor = int(cursor)
            result['next_cursor'] = cursor + 10
            if cursor!=0: result['previous_cursor'] = cursor - 10 # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= 20 or len(local_influencers) < 10:
                result['next_cursor'] = 0
            if cursor <=10 and cursor !=0:
                result['previous_cursor'] = -1

            result['local_influencers'] = local_influencers
    else:
        result['error'] = "Topic not found"
    return json.dumps(result, indent=4)

def getAudienceSample(topic_id, location, cursor):
    '''
    returns maximum 100 audience members for the given topic and location; 10 in each page.
    if next_cursor = 0, you are on the last page.
    '''
    result = {}
    try:
        topic_id = int(topic_id)
    except:
        result['error'] = "Topic does not exist."
        return json.dumps(result, indent=4)
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            try:
                cur.execute(sql, [topic_id])
                var = cur.fetchall()
                topic_name = var[0][0]
            except:
                result['error'] = "Topic does not exist."
                return json.dumps(result, indent=4)

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

            cursor = int(cursor)
            result['next_cursor'] = cursor + 10
            if cursor!=0: result['previous_cursor'] = cursor - 10 # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= 100 or len(audience_sample) < 10:
                result['next_cursor'] = 0
            if cursor <=10 and cursor!=0:
                result['previous_cursor'] = -1

            result['audience_sample'] = audience_sample

    else:
        result['error'] = "Topic not found."
    return json.dumps(result, indent=4)

def getEvents(topic_id, sortedBy, location, cursor):
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
        try:
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]
        except:
            result['error'] = "Topic does not exist."
            return json.dumps(result, indent=4)

        events = [] # all events to be returned
        match = {'end_time': {'$gte': time.time()}}
        sort = {}

        result['topic'] = topic_name
        result['location'] = location

        cursor = int(cursor)

        # SORT CRITERIA
        if sortedBy == 'interested':
            sort['interested']=-1
        elif sortedBy == 'date' or sortedBy=='':
            sort['start_time']=1
        else:
            return {'error': "please enter a valid sortedBy value."}

        print("Location: " + str(location))
        if location !="" and location.lower()!="global":
            print("Filtering and sorting by location")
            EVENT_LIMIT = 70
            COUNTRY_LIMIT=80
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
                  if count ==0:
                      count+=1
                      continue
                  print("Checking db for country (#" + str(count) + "): " + str(country))

                  #match['predicted_place']= country
                  match['place'] = location_regex.getLocationRegex(country)

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

            #pprint.pprint([e['place'] for e in events])
            display_events= events[cursor:cursor+10]

            result['next_cursor'] = cursor + 10
            if cursor!=0: result['previous_cursor'] = cursor - 10 # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= min(EVENT_LIMIT,100) or len(display_events) < 10:
                result['next_cursor'] = 0
            if cursor <=10 and cursor!=0:
                result['previous_cursor'] = -1

            result['events'] = display_events

        else:
            print("returning all events...")
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

            cursor = int(cursor)
            result['next_cursor'] = cursor + 10
            if cursor!=0: result['previous_cursor'] = cursor - 10 # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= 100 or len(events) < 10:
                result['next_cursor'] = 0
            if cursor <=10 and cursor!=0:
                result['previous_cursor'] = -1

            result['events']= events

        return result
