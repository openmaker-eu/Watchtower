import sys
import time
from datetime import datetime

sys.path.insert(0,'/root/cloud')

import facebook
import requests

from application.Connections import Connection

from decouple import config

def mineEventsFromMeetUp(topicList):
    mtup_token = config("MEET_UP_TOKEN")
    mtup_result_events = []
    for topic in topicList:
        url_mtup = "https://api.meetup.com/"
        auth = {"sign":"true", "key":mtup_token}
        mtup_params = {"order":"time", "text":topic, "only":"events", "fields":"featured_photo"}
        mtup_params.update(auth)
        
        response = requests.get(url_mtup + "find/upcoming_events", params = mtup_params)
        response = response.json()
        
        mtup_response_events = response["events"]
        
        for event in mtup_response_events:
            event["place"] = event.get("venue",{}).get("city","-") + ", " + event.get("venue",{}).get("country","")
            event["link"] = event.get("link","")
            event["name"] = event.get("name","")
            event["cover"] = event.get("featured_photo",{}).get("photo_link",None)
            event["interested"] = -1
            event["coming"] = event.get("yes_rsvp_count","")
            event["start_time"] = time.mktime(datetime.strptime(event.get("local_date","0000-00-00") + event.get("local_time","00:00"), "%Y-%m-%d%H:%M").timetuple())
            event["start_date"] = datetime.fromtimestamp(event["start_time"]).strftime("%d-%m-%Y")
            event["end_time"] = event["start_time"] + (event.get("duration",0) / 1e3)
            event["end_date"] = datetime.fromtimestamp(event["end_time"]).strftime("%d-%m-%Y")
            #adding '+0000' to time to be compatible with facebook results
            event["updated_time"] = str(datetime.fromtimestamp(event["created"] / 1e3).strftime("%Y-%m-%dT%H:%M:%S")) + "+0000"
            mtup_result_events.append((event, event["id"]))
        
    return mtup_result_events

def mineEventsFromEventBrite(topicList):
    print("Getting events from Eventbrite...")
    my_token = config("EVENT_BRITE_TOKEN")
    result_events = []
    for topic in topicList:
        print("Processing topic: " + str(topic))
        page_number = 1
        events = []
        while (1):
            print("Fetching page " + str(page_number))
            response = requests.get(
                "https://www.eventbriteapi.com/v3/events/search/",
                headers={
                    "Authorization": "Bearer " + my_token,
                },
                params={
                    'q': topic,
                    'page': page_number
                },
                verify=True,  # Verify SSL certificate
            )
            response = response.json()
            events.extend(response['events'])
            print("# EVENTS:" + str(len(events)))
            if page_number == response['pagination']['page_count']:  # retrieved last page, break the loop.
                break
            page_number += 1

        for event in events:
            try:
                location = requests.get(
                    "https://www.eventbriteapi.com/v3/venues/" + event['venue_id'],
                    headers={
                        "Authorization": "Bearer " + my_token,
                    },
                    params={
                        'q': topic
                    },
                    verify=True,  # Verify SSL certificate
                ).json()
                event['place'] = ''
                if 'address' in location:
                    event['place'] = location['address']['city'] + ", " + location['address']['country']
            except:
                event['place'] = ''
            if 'end' in event and 'utc' in event['end']:
                event['end_time'] = time.mktime(datetime.strptime(event['end']['utc'][:10], "%Y-%m-%d").timetuple())
            else:
                event['end_time'] = time.mktime(datetime.strptime(event['created'][:10], "%Y-%m-%d").timetuple())
            event['start_time'] = event['start']['utc'][:10]
            start_time = time.mktime(datetime.strptime(event['start']['utc'][:10], "%Y-%m-%d").timetuple())
            event['start_date'] = datetime.fromtimestamp(start_time).strftime('%d-%m-%Y')
            event['end_date'] = datetime.fromtimestamp(event['end_time']).strftime('%d-%m-%Y')
            event['link'] = event['url']
            event['name'] = event['name']['text']
            event['cover'] = None
            event['updated_time'] = str(event['changed'])[:-1] + "+0000"
            event['interested'] = -1
            event['coming'] = -1
            if event['logo'] is not None:
                event['cover'] = event['logo']['original']['url']

            result_events.append((event, event['id']))
        
    return result_events

def mineEventsFromFacebook(topicList):
    my_token = config("FACEBOOK_TOKEN")
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")
    fb_result_events = []
    for topic in topicList:
    
        response = graph.get_object('search?q=' + topic +
                                    '&type=event&limit=100&fields=attending_count,updated_time,cover,end_time,id,interested_count,name,place,start_time')
        
        #traverse pagination of response
        while True:
            try:
                for event in response['data']:
                    event["place"] = event.get("place",{}).get("location",{}).get("city","-") + ", " + event.get("place",{}).get("location",{}).get("country","-")
                    event["link"] = 'https://www.facebook.com/events/' + event['id']
                    event["name"] = event.get("name","")
                    event["cover"] = event.get("cover",{}).get("source",None)
                    event["interested"] = event.get("interested_count", -1)
                    event["coming"] = event.get("attending_count","")
                    event["start_time"] = time.mktime(datetime.strptime(event.get("start_time","0000-00-00")[:10], "%Y-%m-%d").timetuple())
                    event["start_date"] = datetime.fromtimestamp(event["start_time"]).strftime('%d-%m-%Y')
                    event["end_time"] = time.mktime(datetime.strptime(event.get("end_time","0000-00-00")[:10], "%Y-%m-%d").timetuple())
                    event["end_date"] = datetime.fromtimestamp(event["end_time"]).strftime('%d-%m-%Y')
                    fb_result_events.append((event, event["id"]))
                response = requests.get(response['paging']['next']).json()
            except:
                break
    return fb_result_events

def insertEventsIntoDataBase(eventsWithIds, topic_id):
    for event, ids in eventsWithIds:
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'id': ids}},
            {'$limit': 1}
        ])

        if ret.alive:
            for elem in ret:
                newEventUpdateTime = datetime.strptime(event['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
                oldEventUpdateTime = datetime.strptime(elem['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
                if newEventUpdateTime != oldEventUpdateTime:
                    print(newEventUpdateTime)
                    print(oldEventUpdateTime)
                if newEventUpdateTime > oldEventUpdateTime:
                    Connection.Instance().events[str(topic_id)].remove({'id': ids})
                    Connection.Instance().events[str(topic_id)].insert_one(event)
                    print('updated')
                else:
                    print('existing')
        else:
            Connection.Instance().events[str(topic_id)].insert_one(event)
            print('added new')

def startEvent(topic_id, topicList):

    eventsFromEventBrite = mineEventsFromEventBrite(topicList)
    eventsFromFacebook = mineEventsFromFacebook(topicList)
    eventsFromMeetUp = mineEventsFromMeetUp(topicList)
    
    insertEventsIntoDataBase(eventsFromEventBrite, topic_id)
    insertEventsIntoDataBase(eventsFromFacebook, topic_id)
    insertEventsIntoDataBase(eventsFromMeetUp, topic_id)


if __name__ == '__main__':

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topics.topic_id, topics.keywords "
            "FROM topics;"
        )
        cur.execute(sql)
        var = cur.fetchall()

    for v in var:
        print(v[0])
        startEvent(v[0], v[1].split(","))


"""
  _____  ______ _______     _______ _      ______ 
 |  __ \|  ____/ ____\ \   / / ____| |    |  ____|
 | |__) | |__ | |     \ \_/ / |    | |    | |__   
 |  _  /|  __|| |      \   /| |    | |    |  __|  
 | | \ \| |___| |____   | | | |____| |____| |____ 
 |_|  \_\______\_____|  |_|  \_____|______|______|
                                                  
                                                  
def idsFromFacebook(topicList):
    my_token = config("FACEBOOK_TOKEN")
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    allSearches = []
    for topic in topicList:
        events = []
        s = graph.get_object('search?q=' + topic + '&type=event&limit=100')
        while True:
            try:
                for search in s['data']:
                    allSearches.append(search['id'])
                s = requests.get(s['paging']['next']).json()
            except:
                break
        allSearches.append({
            'events': events
        })
    return allSearches

def mineEventsFromFacebook(search_id_list, isPreview):
    my_token = config("FACEBOOK_TOKEN")
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")
    t = []
    c = 0
    for ids in search_id_list:
        c += 1
        print(ids)

        event = graph.get_object(
            ids + '?fields=attending_count,updated_time,cover,end_time,id,interested_count,name,place,start_time',
            page=True, retry=5)
        if 'end_time' in event:
            event['end_time'] = time.mktime(datetime.strptime(event['end_time'][:10], "%Y-%m-%d").timetuple())
        else:
            event['end_time'] = time.mktime(datetime.strptime(event['start_time'][:10], "%Y-%m-%d").timetuple())
        try:
            if 'location' in event['place']:
                event['place'] = event['place']['location']['city'] + ", " + event['place']['location']['country']
            else:
                event['place'] = event['place']['name']
        except:
            event['place'] = ''
        event['link'] = 'https://www.facebook.com/events/' + event['id']
        event['start_time'] = event['start_time'][:10]
        start_time = time.mktime(datetime.strptime(event['start_time'][:10], "%Y-%m-%d").timetuple())
        event['start_date'] = datetime.fromtimestamp(start_time).strftime('%d-%m-%Y')
        event['end_date'] = datetime.fromtimestamp(event['end_time']).strftime('%d-%m-%Y')
        event['interested'] = event.pop('interested_count')
        event['coming'] = event.pop('attending_count')
        if 'cover' in event:
            event['cover'] = event['cover']['source']

        t.append((event, ids))
        if c == 5:
            break

    return t    


"""