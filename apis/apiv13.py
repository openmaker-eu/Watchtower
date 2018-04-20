# Author: Kemal Berk Kocabagli

import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))

from application.utils.basic import *
from application.utils import general

from application.Connections import Connection
from predict_location.predictor import Predictor # for location

def getLocalInfluencers(topic_id, location, cursor):
    '''
    returns maximum 20 local influencers for the given topic and location; 10 in each page.
    if next_cursor = 0, you are on the last page.
    '''
    result = {}
    cursor_range = 10
    max_cursor = 20
    cursor = int(cursor)
    if cursor >= max_cursor:
        result['local_influencers']=[]
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            # CHECK TOPIC
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

            location = location.lower()
            # error handling needed for location
            with Connection.Instance().get_cursor() as cur:
                # GET LOCATION
                sql = (
                    "SELECT location_code "
                    "FROM relevant_locations "
                    "WHERE location_name = %s "
                    "OR location_code = %s;"
                )
                try:
                    cur.execute(sql, [location, location])
                    location = cur.fetchall()[0][0]
                except:
                    result['error'] = "Location does not exist."
                    return result

                # GET HIDDEN INFLUENCERS
                sql = (
                    "SELECT influencer_id "
                    "FROM hidden_influencers "
                    "WHERE country_code = %s and topic_id = %s "
                )
                try:
                    cur.execute(sql, [str(location), int(topic_id)])
                    hidden_ids = [int(influencer_id[0]) for influencer_id in cur.fetchall()]
                except:
                    result['error'] = "Problem in fetching hidden influencers for current topic and location."
                    return result

            collection = Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)]

            if location == "global":
                collection = Connection.Instance().influencerDB[str(topic_id)]

            local_influencers = list(
                collection.find({'id': {'$nin':hidden_ids}},
                                {'_id': False,
                                 'name':1,
                                 'screen_name':1,
                                 'description':1,
                                 'location':1,
                                 'time-zone':1,
                                 'lang':1,
                                 'profile_image_url_https':1
                                 })[cursor:min(cursor+cursor_range,max_cursor)]
            )

            result['topic'] = topic_name
            result['location'] = location

            result['next_cursor'] = cursor + (cursor_range-cursor%cursor_range)
            if cursor!=0: result['previous_cursor'] = cursor - cursor_range if cursor%cursor_range == 0 else cursor - cursor%cursor_range # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= max_cursor or len(local_influencers) < cursor_range:
                result['next_cursor'] = 0
            if 'previous_cursor' in result:
                if result['previous_cursor']  == 0:
                    result['previous_cursor']  = -1
            result['next_cursor_str'] = str(result['next_cursor'])

            result['local_influencers'] = local_influencers
    else:
        result['error'] = "Topic not found"
    return result

def getAudienceSample(topic_id, location, cursor):
    '''
    returns maximum 100 audience members for the given topic and location; 10 in each page.
    if next_cursor = 0, you are on the last page.
    '''
    result = {}
    cursor_range = 10
    max_cursor = 100
    cursor = int(cursor)
    if cursor >= max_cursor:
        result['audience_sample']=[]
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result
    try:
        topic_id = int(topic_id)
    except:
        result['error'] = "Topic does not exist."
        return result
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
                return result

            # error handling needed for location
            print("Location: " + str(location))
            location = location.lower()

            # error handling needed for location
            with Connection.Instance().get_cursor() as cur:
                sql = (
                    "SELECT location_code "
                    "FROM relevant_locations "
                    "WHERE location_name = %s "
                    "OR location_code = %s;"
                )
                try:
                    cur.execute(sql, [location, location])
                    location = cur.fetchall()[0][0]
                except:
                    result['error'] = "Location does not exist."
                    return result

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
                                                                                                 })[cursor:min(cursor+cursor_range,max_cursor)]
            )

            result['topic'] = topic_name
            result['location'] = location

            result['next_cursor'] = cursor + (cursor_range-cursor%cursor_range)
            if cursor!=0: result['previous_cursor'] = cursor - cursor_range if cursor%cursor_range == 0 else cursor - cursor%cursor_range # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= max_cursor or len(audience_sample) < cursor_range:
                result['next_cursor'] = 0
            if 'previous_cursor' in result:
                if result['previous_cursor']  == 0:
                    result['previous_cursor']  = -1
            result['next_cursor_str'] = str(result['next_cursor'])

            result['audience_sample'] = audience_sample

    else:
        result['error'] = "Topic not found."
    return result

def getEvents(topic_id, sortedBy, location, cursor, event_ids):
    cursor_range = 10
    max_cursor = 100
    cursor = int(cursor)
    result = {}
    match = {}
    sort = {}
    events = []  # all events to be returned
    cursor_updated=  False

    location = location.lower()
    no_topic_id = False

    if cursor >= max_cursor:
        result['events']=[]
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result

    # SORT CRITERIA
    if sortedBy == 'interested':
        sort['interested']=-1
    elif sortedBy == 'date' or sortedBy=='':
        sort['start_time']=1
    else:
        return {'error': "please enter a valid sortedBy value."}

    # if event ids are entered, ignore all other filters. Only return the requested events.
    if event_ids is not None:
        print("Fetching specific events...")
        topics=dict()
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id, topic_name "
                "FROM topics "
            )
            try:
                cur.execute(sql)
                for topic_id, topic_name in cur.fetchall():
                    topics[topic_id]=topic_name
            except:
                print("Problem with fetching topics.")

        for colname in Connection.Instance().events.collection_names():
            evs = list(Connection.Instance().events[colname].aggregate([
                {'$match': {'id': {'$in': event_ids}}},
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
            # {'$skip': int(cursor)},
                # {'$limit': 10}
            ]))

            for e in evs:
                e['topic'] = topics[int(colname)]
            events += evs
            
            e_ids = set([e['id'] for e in evs])
            if len(set(event_ids) - e_ids) == 0:
                break
        result['topic'] = "All topics"

    else:
        try:
            topic_id = int(topic_id)
        except:
            if event_ids is None:
                result['error'] = "Either topic id or event ids should be provided."
                return result

        # A topic_id is provided
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
                result['topic'] = topic_name

            except:
                if no_topic_id:
                    print("Topic was not provided.")
                else:
                    print("Provided topic does not exist.")
                    return {'error': 'Topic does not exist and no event ids are provided.'}

        result['location'] = location
        match['end_time'] = {'$gte': time.time()}

        print("Location: " + str(location))
        if location !="" and location.lower()!="global":
            #location_predictor = Predictor()
            #location = location_predictor.predict_location(location)
            if location == "italy": location = "it"
            elif location == "spain": location = "es"
            elif location == "slovakia": location = "sk"
            elif location == "uk": location = "gb"
            elif location == "turkey": location = "tr"

            print("Filtering and sorting by location: " + location)
            EVENT_LIMIT = 70
            COUNTRY_LIMIT=80
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

                    match['$or'] = [{'place':location_regex.getLocationRegex(country)},{'predicted_place':country}]
                    match['link'] = {'$nin': hidden_event_links}

                    events += list(Connection.Instance().events[str(topic_id)].aggregate([
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
                        {'$sort': sort}
                        # {'$skip': int(cursor)},
                        # {'$limit': 10}
                    ]))

                    count+=1
                    print("length:" + str(len(events)))
                    if len(events) >= min(cursor+cursor_range,EVENT_LIMIT):
                        break
                    if (count > COUNTRY_LIMIT):
                        break

            #pprint.pprint([e['place'] for e in events])
            display_events = events[cursor:min(cursor+cursor_range,max_cursor)]

            result['next_cursor'] = cursor + (cursor_range-cursor%cursor_range)
            if cursor!=0: result['previous_cursor'] = cursor - cursor_range if cursor%cursor_range == 0 else cursor - cursor%cursor_range # if we are on the first page, there is no previous cursor

            # cursor boundary checks
            if result['next_cursor']  >= min(EVENT_LIMIT,max_cursor) or len(display_events) < cursor_range:
                result['next_cursor'] = 0
            if 'previous_cursor' in result:
                if result['previous_cursor']  == 0:
                    result['previous_cursor']  = -1

            result['next_cursor_str'] = str(result['next_cursor'])
            cursor_updated=True

            events = display_events

        else:
            print("returning all events...")
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
                {'$skip': int(cursor)},
                {'$limit': min(cursor_range, max_cursor - cursor)}
            ]))

    # CURSOR CHECK AND UPDATE
    if not cursor_updated:
        cursor = int(cursor)
        result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
        if cursor != 0: result[
            'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

        if result['next_cursor'] >= max_cursor or len(events) < cursor_range:
            result['next_cursor'] = 0
        if 'previous_cursor' in result:
            if result['previous_cursor'] == 0:
                result['previous_cursor'] = -1

        result['next_cursor_str'] = str(result['next_cursor'])

    # Correct date time format
    for event in events:
        if not isinstance(event['start_time'],str):
            event['start_time'] = datetime.datetime.utcfromtimestamp(event['start_time']).strftime('%Y-%m-%dT%H:%M:%SZ')
        if not isinstance(event['end_time'],str):
            event['end_time'] = datetime.datetime.utcfromtimestamp(event['end_time']).strftime('%Y-%m-%dT%H:%M:%SZ')

    result['events'] = events

    return result


def getNewsFeeds(date, cursor, forbidden_domain, topics):
    result = {}
    cursor_range = 20
    max_cursor = 60
    cursor = int(cursor)

    if topics == [""]:
        return {}

    if cursor >= max_cursor:
        result['news']=[]
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result

    dates = ['yesterday', 'week', 'month']
    if date not in dates:
        result['Error'] = 'invalid date'
        return result

    # feeds = list(Connection.Instance().filteredNewsPoolDB[themeid].find({'name': date}, {date: 1}))
    # feeds = list(feeds[0][date][cursor:cursor+20])

    #date = general_utils.determine_date(date)

    news = []
    for topic_id in topics:
        #if len(news) >= cursor + 20:
        #    break
        #news = news + date_filter.getDateList(topic_id, int(date), forbidden_domain)
        feeds = list(Connection.Instance().filteredNewsPoolDB[str(topic_id)].find({'name': date}, {date: 1}))
        if len(feeds) > 0:
            news = news + feeds[0][date]

    news = news[cursor:min(cursor+cursor_range,max_cursor)]
    result['next_cursor'] = cursor + (cursor_range-cursor%cursor_range)

    if cursor!=0: result['previous_cursor'] = cursor - cursor_range if cursor%cursor_range == 0 else cursor - cursor%cursor_range # if we are on the first page, there is no previous cursor

    # cursor boundary checks
    if result['next_cursor']  >= max_cursor or len(news) < cursor_range:
        result['next_cursor'] = 0
    if 'previous_cursor' in result:
        if result['previous_cursor']  == 0:
            result['previous_cursor']  = -1

    result['next_cursor_str'] = str(result['next_cursor'])
    result['news'] = news

    return result


def getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor, since, until,
            domains, topics):
    result = {}
    cursor = int(cursor)
    cursor_range = 20
    max_cursor = 60
    if cursor >= max_cursor:
        result['news']=[]
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result
    if topics ==[""] and news_ids == [""] and keywords == [""] and since == "" and until == "" and \
                    languages == [""] and cities == [""] and countries == [""] and user_location == [""] \
            and user_language == [""] and domains == [""]:
        return {'news': [], 'next_cursor': 0, 'next_cursor_str': "0"}

    aggregate_dictionary = []
    find_dictionary = {}
    date_dictionary = {}

    if news_ids != [""]:
        news_ids_in_dictionary = [int(one_id) for one_id in news_ids]
        find_dictionary['link_id'] = {'$in': news_ids_in_dictionary}

    if keywords != [""]:
        keywords_in_dictionary = [re.compile(key, re.IGNORECASE) for key in keywords]
        find_dictionary['$or'] = [{'title': {'$in': keywords_in_dictionary}},
                                  {'summary': {'$in': keywords_in_dictionary}},
                                  {'full_text': {'$in': keywords_in_dictionary}}]

    if domains != [""]:
        domains_in_dictionary = [re.compile(key, re.IGNORECASE) for key in domains]
        find_dictionary['domain'] = {'$nin': domains_in_dictionary}

    if languages != [""]:
        language_dictionary = [lang for lang in languages]
        find_dictionary['language'] = {'$in': language_dictionary}

    if cities != [""]:
        city_dictionary = [re.compile(city, re.IGNORECASE) for city in cities]
        find_dictionary['location.cities'] = {'$in': city_dictionary}
        aggregate_dictionary.append({'$unwind': '$location.cities'})

    if countries != [""]:
        country_dictionary = [re.compile(country, re.IGNORECASE) for country in countries]
        find_dictionary['location.countries'] = {'$in': country_dictionary}
        aggregate_dictionary.append({'$unwind': '$location.countries'})

    if user_location != [""]:
        user_location_dictionary = [re.compile(city, re.IGNORECASE) for city in user_location]
        find_dictionary['mentions.location'] = {'$in': user_location_dictionary}
        aggregate_dictionary.append({'$unwind': '$mentions'})

    if user_language != [""]:
        user_language_dictionary = [re.compile(country, re.IGNORECASE) for country in user_language]
        find_dictionary['mentions.language'] = {'$in': user_language_dictionary}
        aggregate_dictionary.append({'$unwind': '$mentions'})

    if since != "":
        try:
            since_in_dictionary = datetime.strptime(since, "%d-%m-%Y")
            date_dictionary['$gte'] = since_in_dictionary
        except ValueError:
            return {'error': "please, enter a valid since day. DAY-MONTH-YEAR"}

    if until != "":
        try:
            until_in_dictionary = datetime.strptime(until, "%d-%m-%Y")
            date_dictionary['$lte'] = until_in_dictionary
        except ValueError:
            return {'error': "please, enter a valid since day. DAY-MONTH-YEAR"}

    if date_dictionary != {}:
        find_dictionary['published_at'] = date_dictionary

    aggregate_dictionary.append({'$match': find_dictionary})
    if user_language == [""] and user_location == [""]:
        aggregate_dictionary.append({'$project': {'mentions': 0}})
    aggregate_dictionary.append({'$project': {'_id': 0, 'bookmark': 0, 'bookmark_date': 0, 'location': 0}})

    aggregate_dictionary.append({'$sort': {'link_id': -1}})

    print(aggregate_dictionary)

    topics_filter = []
    if topics != [""]:
        topics_filter = [int(one_id) for one_id in topics]

    news = []
    for alertid in Connection.Instance().newsPoolDB.collection_names():
        if alertid != "counters":
            if len(news) >= cursor + cursor_range:
                break
            if topics_filter == []:
                news = news + list(Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary, allowDiskUse= True))
            else:
                if int(alertid) in topics_filter:
                    news = news + list(Connection.Instance().newsPoolDB[str(alertid)].aggregate(aggregate_dictionary, allowDiskUse= True))

    news = news[cursor:min(cursor+cursor_range,max_cursor)]

    result['next_cursor'] = cursor + (cursor_range-cursor%cursor_range)
    if cursor!=0: result['previous_cursor'] = cursor - cursor_range if cursor%cursor_range == 0 else cursor - cursor%cursor_range # if we are on the first page, there is no previous cursor

    # cursor boundary checks
    if result['next_cursor']  >= max_cursor or len(news) < cursor_range:
        result['next_cursor'] = 0
    if 'previous_cursor' in result:
        if result['previous_cursor']  == 0:
            result['previous_cursor']  = -1

    result['next_cursor_str'] = str(result['next_cursor'])
    result['news'] = news

    return json.dumps(result, default=general.date_formatter, indent=4)


def getChallenges(is_open, date, cursor):
    result = {}
    cursor = int(cursor)
    cursor_range = 10
    max_cursor = 60
    if cursor >= max_cursor:
        result['news'] = []
        result['error'] = "Cannot exceed max cursor = " + str(max_cursor) + "."
        return result

    match = dict()
    if is_open:
        match['status'] = "OPEN"

    challenges = list(Connection.Instance().challengesDB['innocentive'].aggregate([
        {'$match': match},
        {'$project': {
            '_id':0
        }}
    ])
    )
    challenges = challenges[cursor:min(cursor + cursor_range, max_cursor)]

    result['next_cursor'] = cursor + (cursor_range - cursor % cursor_range)
    if cursor != 0: result[
        'previous_cursor'] = cursor - cursor_range if cursor % cursor_range == 0 else cursor - cursor % cursor_range  # if we are on the first page, there is no previous cursor

    # cursor boundary checks
    if result['next_cursor'] >= max_cursor or len(challenges) < cursor_range:
        result['next_cursor'] = 0
    if 'previous_cursor' in result:
        if result['previous_cursor'] == 0:
            result['previous_cursor'] = -1

    result['next_cursor_str'] = str(result['next_cursor'])
    result['challenges'] = challenges

    return result