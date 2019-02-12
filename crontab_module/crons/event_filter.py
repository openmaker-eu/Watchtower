import sys
from time import gmtime, strftime, time
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))

from application.utils.basic import *
from application.utils import general
import pandas as pd
from predict_location.predictor import Predictor # for location

from application.Connections import Connection

def getEvents(topic_id, sortedBy, location):
    result = {}
    match = {}
    sort = {}
    events = []  # all events to be returned

    location = location.lower()

    # SORT CRITERIA
    if sortedBy == 'interested':
        sort['interested']=-1
    elif sortedBy == 'date':
        sort['start_time']=1

    result['location'] = location
    match['end_time'] = {'$gte': time()}

    if location.lower()!="global":
        location_predictor = Predictor()
        location = location_predictor.predict_location(location)
        cdl = []

        # GET HIDDEN EVENTS
        with Connection.Instance().get_cursor() as cur:
            hidden_event_links=[]

            try:
                colnames = Connection.Instance().events.collection_names() if no_topic_id else [topic_id]
                for colname in colnames:
                    print(colname)
                    sql = (
                        "SELECT event_link "
                        "FROM hidden_events "
                        "WHERE topic_id = %s "
                    )
                    cur.execute(sql, [int(colname)])
                    hidden_event_links.extend(str(event[0]) for event in cur.fetchall())
                    print(hidden_event_links)
            except:
                result['error'] = "Problem in fetching hidden events for current topic."
                return result

        location = location.upper()
        distance_matrix = pd.read_csv('distance-matrix.csv.gz')
        distance_matrix.fillna('NA', inplace=True)
        distances = distance_matrix.sort_values(location)[[location, 'Country']].values


        for distance, country in distances:
            match['$or'] = [{'place':location_regex.getLocationRegex(country)},{'predicted_place':country}]
            match['link'] = {'$nin': hidden_event_links}

            new_events = list(Connection.Instance().events[str(topic_id)].aggregate([
                {'$match': match},
                {'$project': {'_id': 0,
                                "updated_time": 1,
                                "cover": 1,
                                "description": 1,
                                "start_time": 1,
                                "end_time": 1,
                                "id": 1,
                                "name": 1,
                                "place": 1,
                                "link": 1,
                                "interested": 1,
                                "coming": 1
                                }},
                {'$sort': sort},
                {'$limit': 200}
            ], allowDiskUse=True))

            new_events = [{**event, 'distance': distance, 'country': country.lower()} for event in new_events]

            events += new_events

    else:
        events = list(Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': match},
            {'$project': {'_id': 0,
                            "updated_time": 1,
                            "cover": 1,
                            "end_time": 1,
                            "description": 1,
                            "id": 1,
                            "name": 1,
                            "place": 1,
                            "start_time": 1,
                            "link": 1,
                            "interested": 1,
                            "coming": 1
                            }},
            {'$sort': sort},
            {'$limit': 200}
        ], allowDiskUse=True))

    # Correct date time format
    for event in events:
        if not isinstance(event['start_time'],str):
            event['start_time'] = datetime.datetime.utcfromtimestamp(event['start_time']).strftime('%Y-%m-%dT%H:%M:%SZ')
        if not isinstance(event['end_time'],str):
            event['end_time'] = datetime.datetime.utcfromtimestamp(event['end_time']).strftime('%Y-%m-%dT%H:%M:%SZ')

    return events

def calc(alertid):
    lookup = {'tr': 'turkey', 'it': 'italy', 'es': 'spain', 'sk': 'slovakia', 'uk': 'gb', 'global': 'global'}
    locations = ["it", "es", "sk", "gb", "tr", "global"]
    sorted_by = ["interested", "date"]
    for location in locations:
        for sort_key in sorted_by:
            result = {
                'name': location,
                'sort': sort_key,
                lookup[location]: getEvents(alertid, sort_key, location),
                'modified_date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())
            }
            if lookup[location]:
                Connection.Instance().filteredEventsPoolDB[str(alertid)].remove({'name': result['name'], 'sort': result['sort']})
                Connection.Instance().filteredEventsPoolDB[str(alertid)].insert_one(result)


if __name__ == '__main__':
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM topics"
        )
        cur.execute(sql)
        alert_list = cur.fetchall()
        for alert in alert_list:
            print(alert[0])
            calc(alert[0])
