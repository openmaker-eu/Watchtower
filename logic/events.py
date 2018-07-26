__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

import csv
import re
import time

from application.Connections import Connection
from datetime import datetime


def get_events(topic_id, sortedBy, location, cursor):
    cursor_range = 10
    max_cursor = 100
    cursor = int(cursor)
    result = {}
    events = []
    location = location.lower()
    if cursor >= max_cursor:
        result['events'] = []
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result
    try:
        topic_id = int(topic_id)
    except:
        result['event'] = "topic not found"
        return result
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
            return result

        events = []  # all events to be returned
        match = {'end_time': {'$gte': time.time()}}
        sort = {}

        result['topic'] = topic_name
        result['location'] = location

    # SORT CRITERIA
    if sortedBy == 'interested':
        sort['interested'] = -1
    elif sortedBy == 'date' or sortedBy == '':
        sort['start_time'] = 1
    else:
        return {'error': "please enter a valid sortedBy value."}

    print("Location: " + str(location))
    if location != "" and location.lower() != "global":
        # location_predictor = Predictor()
        # location = location_predictor.predict_location(location)
        if location == "italy":
            location = "it"
        elif location == "spain":
            location = "es"
        elif location == "slovakia":
            location = "sk"
        elif location == "uk":
            location = "gb"
        elif location == "turkey":
            location = "tr"

        print("Filtering and sorting by location: " + location)
        EVENT_LIMIT = 70
        COUNTRY_LIMIT = 80
        cdl = []

        with open('../rank_countries.csv', 'r') as f:
            reader = csv.reader(f)
            country_distance_lists = list(reader)
            for i in range(len(country_distance_lists)):
                if country_distance_lists[i][0] == location:
                    cdl = country_distance_lists[i]
            print("Found cdl!")
        count = 0
        for country in cdl[1:]:
            match['$or'] = [{'place': re.compile("^.*\\b" + country + "$", re.IGNORECASE)},
                            {'predicted_place': country}]
            events_in_current_location = list(Connection.Instance().events[str(topic_id)].aggregate([
                {'$match': match},
                {'$project': {'_id': 0,
                              "updated_time": 1,
                              "cover": 1,
                              "end_time": 1,
                              "description": 1,
                              "start_date": 1,
                              "end_date": 1,
                              "id": 1,
                              "name": 1,
                              "place": 1,
                              "start_time": 1,
                              "link": 1,
                              "interested": 1,
                              "coming": 1
                              }},
                {'$sort': sort}
                # {'$skip': int(cursor)},
                # {'$limit': 10}
            ]))
            events += events_in_current_location
            count += 1
            message = "Checked db for country (#" + str(count) + "): " + str(country)
            if len(events_in_current_location) > 0:
                message += " + " + str(len(events_in_current_location)) + " events!"

            print(message)

            print("length:" + str(len(events)))
            if len(events) >= min(cursor + cursor_range, EVENT_LIMIT):
                break
            if count > COUNTRY_LIMIT:
                print("Searched closest " + str(COUNTRY_LIMIT) + " countries. Stopping here.")
                break

        # pprint.pprint([e['place'] for e in events])
        display_events = events[cursor:min(cursor + cursor_range, max_cursor)]

        result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
        if cursor != 0: result[
            'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

        # cursor boundary checks
        if result['next_cursor'] >= min(EVENT_LIMIT, max_cursor) or len(display_events) < cursor_range:
            result['next_cursor'] = 0
        if 'previous_cursor' in result:
            if result['previous_cursor'] == 0:
                result['previous_cursor'] = -1

        result['next_cursor_str'] = str(result['next_cursor'])
        result['events'] = display_events

    else:
        print("returning all events...")
        events = list(Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': match},
            {'$project': {'_id': 0,
                          "updated_time": 1,
                          "cover": 1,
                          "end_time": 1,
                          "description": 1,
                          "start_date": 1,
                          "end_date": 1,
                          "id": 1,
                          "name": 1,
                          "place": 1,
                          "start_time": 1,
                          "link": 1,
                          "interested": 1,
                          "coming": 1
                          }},
            {'$sort': sort},
            {'$skip': int(cursor)},
            {'$limit': min(cursor_range, max_cursor - cursor)}
        ]))

        cursor = int(cursor)
        result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
        if cursor != 0: result[
            'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

        # cursor boundary checks
        if result['next_cursor'] >= max_cursor or len(events) < cursor_range:
            result['next_cursor'] = 0
        if 'previous_cursor' in result:
            if result['previous_cursor'] == 0:
                result['previous_cursor'] = -1

        result['next_cursor_str'] = str(result['next_cursor'])
        result['events'] = events

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT event_link "
            "FROM hidden_events "
            "WHERE topic_id = %s "
        )
        cur.execute(sql, [int(topic_id)])
        hidden_links = [str(event_link[0]) for event_link in cur.fetchall()]
        # print("Hidden ids:")
        # print(hidden_ids)
        for event in result['events']:
            if str(event['link']) in hidden_links:
                # print(str(event['link']) + " is hidden")
                event['hidden'] = True
            else:
                event['hidden'] = False
                # print(str(event['link']) + " not hidden")

    for event in result['events']:
        if not isinstance(event['start_time'], str):
            event['start_time'] = datetime.utcfromtimestamp(event['start_time']).strftime('%Y-%m-%dT%H:%M:%SZ')
        if not isinstance(event['end_time'], str):
            event['end_time'] = datetime.utcfromtimestamp(event['end_time']).strftime('%Y-%m-%dT%H:%M:%SZ')

    return result

def hide_event(topic_id, user_id, event_link, description, is_hide):
    # print("in hide influencer:")
    # print(influencer_id)
    print("In hide event")
    print("Topic id:" + str(topic_id))
    event_link = str(event_link)
    print(event_link)
    if is_hide:
        print("Hiding event with link:" + event_link)
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "INSERT INTO hidden_events "
                "(topic_id, event_link, description) "
                "VALUES (%s, %s, %s)"
            )
            cur.execute(sql, [int(topic_id), str(event_link), ""])
    else:
        print("Unhiding event with link:" + event_link)
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "DELETE FROM hidden_events "
                "WHERE topic_id = %s and event_link = %s "
            )
            cur.execute(sql, [int(topic_id), str(event_link)])
