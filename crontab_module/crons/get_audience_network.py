# Author: Kemal Berk Kocabagli
import sys
from decouple import config # to get current working directory
sys.path.insert(0, config("ROOT_DIR"))

from application.utils.basic import *

import tweepy  # Twitter API helper package
from tweepy import OAuthHandler
import pymongo # for pymongo functions
from datetime import datetime # to print the date & time in the output log whenever this script is run OR for time related checks

from application.Connections import Connection

consumer_key = config("TWITTER_CONSUMER_KEY") # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# Decorator for measuring execution time of functions
def timeit(method):
    def timed(*args, **kw):
        start = time.time()
        result = method(*args, **kw)
        end = time.time()
        print("... {} seconds".format(end - start))
        return result
    return timed

@timeit
def construct_audience_members(topicID, location):
    regx = location_regex.getLocationRegex(location)
    # upsert many
    operations = []
    for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location':regx},{'id':1,'location':1}):
        operations.append(
               pymongo.UpdateOne(
               {'id': audience_member['id']},
               {
                '$addToSet':{
                'topics': topicID,
                'locations': audience_member['location'],
                },

                '$setOnInsert' : {
                'last_processed' : None,
                'last_cursor' : None,
                'finished_last_time' : False,
                'followers':[], # initialize followers list empty,
                }
               }, 
               upsert=True)
        )
    #print(operations[:10])
    try:
        Connection.Instance().audience_networks_DB['all_audience_members'].bulk_write(operations, ordered=False)
    except Exception as e:
        print("Exception in bulk_write." + str(e))

def construct_all_audience_members ():
    Connection.Instance().audience_networks_DB['all_audience_members'].create_index("id",unique=True)
    locations = ['italy', 'slovakia', 'spain', 'uk', 'tr'] # relevant locations

    with Connection.Instance().get_cursor() as cur:
        sql = (
        "SELECT topic_id, topic_name "
        "FROM topics "
        )
        cur.execute(sql)
        topics = cur.fetchall() # list of all topics

    print("There are {} many topic-location pairs.".format(len(topics) * len(locations)))
    index = 0
    for topicID,topicName in topics:
        for location in locations:
            print("{}) {}-{}".format(index + 1 , topicName, location) , end='', flush=True)
            index += 1
            construct_audience_members(topicID, location)

def is_processable(member, threshold_in_day):
    # Do we need this or should the script get followers no matter what ???
    if not member:
        return False

    if member["last_processed"] and (datetime.today()- member['last_processed']).days < threshold_in_day:
        return False

    return True

@timeit
def get_network_twitter_profiles(MIN_FOLLOWERS_COUNT, MAX_FOLLOWERS_COUNT):
    network_member_ids = Connection.Instance().audience_networks_DB['all_audience_members'].distinct('id')
    network_members = list(Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': network_member_ids}, 'followers_count':{'$gt':MIN_FOLLOWERS_COUNT,'$lt':MAX_FOLLOWERS_COUNT}}, {'_id':0, 'id':1, 'followers_count':1}))
    return network_members

def get_start_cursor(member):
    if member["last_cursor"]:
        cursor = member['last_cursor']
    else:
        cursor = -1

    tweepy_cursor = tweepy.Cursor(api.followers_ids, id=member["id"], cursor=cursor)

    # if this member is totally processed last time, move one cursor if possible
    if member["finished_last_time"] and tweepy_cursor.iterator.next_cursor != 0:
        cursor = tweepy_cursor.iterator.next_cursor
        tweepy_cursor = tweepy.Cursor(api.followers_ids, id=member["id"], cursor=cursor)

    return (cursor, tweepy_cursor)

def process_member(member):
    print("Processing user : {}".format(member["id"]))
    
    last_cursor, cursor = get_start_cursor(member)

    requests = []

    try:
        for page in cursor.pages():
            if (cursor.iterator.next_cursor != 0):
                last_cursor = cursor.iterator.next_cursor

            requests.append(pymongo.UpdateOne(
                {"id" : member["id"]},
                {
                    "$addToSet" : {"followers" : {"$each" : page}},
                    "$set" : {
                        "last_cursor" : last_cursor,
                        "last_processed" : datetime.today(),
                        "finished_last_time" : (cursor.iterator.next_cursor == 0)
                    }
                }
            ))
    except (tweepy.TweepError , tweepy.error.TweepError) as twperr:
        print(twperr) # in case of errors due to protected accounts

    try:
        if (len(requests)!=0):
            Connection.Instance().audience_networks_DB['all_audience_members'].bulk_write(requests,ordered=False)
    except Exception as e:
        print("Exception in bulk_write:" + str(e))

@timeit
def get_followers_of_network_members(MIN_FOLLOWERS_COUNT, MAX_FOLLOWERS_COUNT):
    print("Getting twitter profiles of the members in the network")
    network_twitter_profiles = get_network_twitter_profiles(MIN_FOLLOWERS_COUNT, MAX_FOLLOWERS_COUNT)

    print("There are {} many members that satisfy given follower count criteria".format(len(network_twitter_profiles)))
    for twitter_profile in network_twitter_profiles:
        member = Connection.Instance().audience_networks_DB['all_audience_members'].find_one({'id':twitter_profile["id"]})

        if is_processable(member,1):
            process_member(member)

def main():
    construct_all_audience_members()

if __name__ == "__main__":
    main()
