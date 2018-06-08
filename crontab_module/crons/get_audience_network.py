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

def get_audience_network(topicID, location):
    start = time.time()
    # filter audience by location
    regx = location_regex.getLocationRegex(location)
    loc_filtered_audience_ids =[]
    try:
        loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id',{'location':regx})
    except Exception as ex:
        print("appending one by one...")
        for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location':regx},{'id':1,'location':1}):
            loc_filtered_audience_ids.append({'id':audience_member['id'], 'location':audience_member['location']})
    print("Filtered audience by location in " + str(time.time()-start) + " seconds.")
    start = time.time()
    # pprint.pprint(loc_filtered_audience_ids[:10])
    audience_member_count=1
    audience_size = len(loc_filtered_audience_ids)
    for audience_member_id in loc_filtered_audience_ids:
        audience_member = Connection.Instance().audience_networks_DB[str(topicID)+"_"+str(location)].find_one({'id':audience_member_id})
        if (audience_member is not None):
            if "last_processed" in audience_member:
                if ((datetime.today()- audience_member['last_processed']).days < 1): # if this audience member is processed today, continue
                    print(str(audience_member_id) + " HAS ALREADY BEEN PROCESSED TODAY.")
                    continue
        else:
            # first time adding this person. Initialize with empty followers list.
            Connection.Instance().audience_networks_DB[str(topicID)+"_"+str(location)].update_one(
                    { 'id': audience_member_id},
                    { '$setOnInsert': {'followers':[]}},
                    upsert=True
            )

        print("Processing audience member (" + str(audience_member_count) + "/" + str(audience_size) + ") with id: " + str(audience_member_id))
        # get all the follower ids page by page
    	# starting from most recent follower
        page_count = 0
        followers_count = 0
        STOP_FLAG= 0
        THRESHOLD = 10
        already_added_ids = []
        cursor = tweepy.Cursor(api.followers_ids, id=audience_member_id, cursor=-1)
        try:
            for page in cursor.pages():
                #pprint.pprint(api.rate_limit_status()['resources']['followers'])
                print("Page length: " + str(len(page)))
                # upsert many
                print("UPSERTING")
                operations = []
                inside_network = [userID for userID in page if userID in loc_filtered_audience_ids]
                for i in range(len(inside_network)): # look at all the ids inside this network who also follow current audience member
                    follower_id = inside_network[i]

                    if Connection.Instance().audience_networks_DB[str(topicID)+"_"+str(location)].count({"$and":[ {"id":audience_member_id}, {"followers":follower_id}]}) != 0:
                        already_added_ids.append(follower_id)
                        print("follower # " + str(i) + " was already added. Follower id: " + str(follower_id))
                    else:
                        already_added_ids=[]
                        print("ALREADY ADDED IDS EMTPIED at follower # " + str(i) + " with follower id: " + str(follower_id))
                        operations.append(
                            pymongo.UpdateOne(
                            { 'id': audience_member_id},
                            { '$addToSet': {'followers': follower_id}
                            }, upsert=True)
                        )
                        followers_count +=1
                    if len(already_added_ids) == THRESHOLD:
                        STOP_FLAG=1
                        break

                print("Writing to MongoDB...")
                # save the followers to MongoDB
                try:
                    # max size of operations will be 5000 (page size).
                    if (len(operations)!=0):
                        Connection.Instance().audience_networks_DB[str(topicID)+"_"+str(location)].bulk_write(operations,ordered=False)
                except Exception as e:
                    print("Exception in bulk_write:" + str(e))

                if STOP_FLAG == 1:
                    page_count +=1
                    print("Stopping at page " + str(page_count-1))
                    print("Followers that resulted in STOP: " + str (already_added_ids))
                    break
                page_count +=1 # increment page count

        except tweepy.TweepError as twperr:
            print(twperr) # in case of errors due to protected accounts
            pass

        print("Processed " + str(page_count) + " page(s).")

        Connection.Instance().audience_networks_DB[str(topicID)+"_"+str(location)].update(
            { 'id': audience_member_id },
            { '$set':{'last_processed': datetime.now(), # update last processed time of this audience member
                    'last_followers_count': audience_member['last_followers_count']+followers_count}
            }
        )

        print("Processed audience_member: " + str(audience_member_id) + " : " + str(followers_count) + " new followers." ) # Processing DONE.
        print("========================================")
        audience_member_count +=1

def construct_all_audience_members ():
    Connection.Instance().audience_networks_DB['all_audience_members'].create_index("id",unique=True)
    locations = ['italy', 'slovakia', 'spain', 'uk'] # relevant locations

    with Connection.Instance().get_cursor() as cur:
        sql = (
        "SELECT topic_id, topic_name "
        "FROM topics "
        )
        cur.execute(sql)
        topics = cur.fetchall() # list of all topics

    for topicID,topicName in topics:
        for location in locations:
            print("================================================================================================")
            print("Getting audience members...  " + ", TOPIC: " + topicName + "(" + str(topicID) + ")" +  " , LOCATION: " + location )
            start = time.time()
            # filter audience by location
            regx = location_regex.getLocationRegex(location)
            # upsert many
            print("UPSERTING")
            operations = []
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location':regx},{'id':1,'location':1}):
                operations.append(
                       pymongo.UpdateOne(
                       { 'id': audience_member['id']},
                       { '$addToSet':{
                       'topics': topicID,
                       'locations': audience_member['location'],
                       'followers':[], # initiate followers list empty,
                       'finished_once':False
                       }
                       }, upsert=True)
                )
            print("Filtered audience by location in " + str(time.time()-start) + " seconds.")
            start = time.time()
            print(operations[:10])
            try:
                Connection.Instance().audience_networks_DB['all_audience_members'].bulk_write(operations, ordered=False)
            except Exception as e:
                print("Exception in bulk_write." + str(e))


def get_followers_of_all_audience_members(MIN_FOLLOWERS_COUNT, MAX_FOLLOWERS_COUNT):
        start = time.time()

        all_audience_member_ids = []
        try:
            all_audience_member_ids = Connection.Instance().audience_networks_DB['all_audience_members'].distinct('id')
        except:
            for all_audience_member_id in Connection.Instance().audience_networks_DB['all_audience_members'].find({},{'_id':0,'id':1}):
                all_audience_member_ids.append(all_audience_member_id)

        all_audience_members = list(Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': all_audience_member_ids}, 'followers_count':{'$gt':MIN_FOLLOWERS_COUNT,'$lt':MAX_FOLLOWERS_COUNT}}, {'_id':0, 'id':1, 'followers_count':1}))
        audience_size = len(all_audience_members)
        audience_member_count=1

        for audience_member in all_audience_members:
            audience_member_id = audience_member['id']

            aud_member = Connection.Instance().audience_networks_DB['all_audience_members'].find_one({'id':audience_member_id})

            if (aud_member is not None):
                if "last_processed" in aud_member:
                    if 'finished_once' in aud_member:
                        if aud_member['finished_once'] == True:
                            # if this audience member is finished once and processed within the last 10 days, continue
                            if ((datetime.today() - aud_member['last_processed']).days < 10):
                                print(str(audience_member_id) + "(finished once) HAS ALREADY BEEN PROCESSED IN LAST 10 DAYS.")
                                audience_member_count+=1
                                continue
                        else:
                            # if this audience member is not finished once and processed today, continue
                            if ((datetime.today()- aud_member['last_processed']).days < 1):
                                print(str(audience_member_id) + " HAS ALREADY BEEN PROCESSED TODAY.")
                                audience_member_count+=1
                                continue

            print("Processing audience member (" + str(audience_member_count) + "/" + str(audience_size) + ") with id: " + str(audience_member_id) + " and followers count: " + str(audience_member['followers_count']))

            start_cursor = -1  # get all the follower ids page by page, starting from most recent follower (first page)
            # if an influencer has not been processed until the end once, start from last cursor.
            if 'finished_once' in aud_member:
                if aud_member['finished_once'] == False:
                    if 'last_cursor' in aud_member:
                        start_cursor = aud_member['last_cursor']

            print("Start cursor value: " + str(start_cursor))

            cursor = tweepy.Cursor(api.followers_ids, id=audience_member_id, cursor=start_cursor)
            last_cursor = start_cursor

            # get all the follower ids page by page
        	# starting from most recent follower
            page_count = 0
            followers_count = 0
            STOP_FLAG= 0
            THRESHOLD = 10
            already_added_ids = []
            cursor = tweepy.Cursor(api.followers_ids, id=audience_member_id, cursor=-1)
            try:
                for page in cursor.pages():
                    if (cursor.iterator.next_cursor != 0):
                        last_cursor = cursor.iterator.next_cursor
                    #pprint.pprint(api.rate_limit_status()['resources']['followers'])
                    print("Page length: " + str(len(page)))
                    # upsert many
                    print("UPSERTING")
                    operations = []
                    for i in range(len(page)):
                        follower_id = page[i]
                        if 'finished_once' in aud_member:
                            if aud_member['finished_once'] == True:
                                if Connection.Instance().audience_networks_DB['all_audience_members'].count({"$and":[ {"id":audience_member_id}, {"followers":follower_id}]}) != 0:
                                    already_added_ids.append(follower_id)
                                    print("follower # " + str(i) + " was already added. Follower id: " + str(follower_id))
                                else:
                                    already_added_ids=[]
                                    print("ALREADY ADDED IDS EMTPIED at follower # " + str(i) + " with follower id: " + str(follower_id))
                                    operations.append(
                                        pymongo.UpdateOne(
                                        { 'id': audience_member_id},
                                        { '$addToSet': {'followers': follower_id}
                                        }, upsert=True)
                                    )
                                    followers_count +=1
                                if len(already_added_ids) == THRESHOLD:
                                    STOP_FLAG=1
                                    break
                            else:
                                operations.append(
                                    pymongo.UpdateOne(
                                    { 'id': audience_member_id},
                                    { '$addToSet': {'followers': follower_id}
                                    }, upsert=True)
                                )
                                followers_count +=1

                    print("Writing to MongoDB...")
                    # save the followers to MongoDB
                    try:
                        # max size of operations will be 5000 (page size).
                        if (len(operations)!=0):
                            Connection.Instance().audience_networks_DB['all_audience_members'].bulk_write(operations,ordered=False)
                    except Exception as e:
                        print("Exception in bulk_write:" + str(e))

                    if STOP_FLAG == 1:
                        page_count +=1
                        print("Stopping at page " + str(page_count-1))
                        print("Followers that resulted in STOP: " + str (already_added_ids))
                        break

                    if aud_member[
                        'finished_once'] == False:  # if we haven't finished processing an the audience member, we need to update the last cursor.
                        Connection.Instance().audience_networks_DB['all_audience_members'].update(
                            {'id': audience_member_id},
                            {'$set': {'last_cursor': last_cursor}}  # update last cursor of this influencer
                        )
                    page_count +=1 # increment page count
                    if cursor.iterator.next_cursor == 0:  # if true, we are at the end of the followers for this influencer.
                        Connection.Instance().audience_networks_DB['all_audience_members'].update(
                            {'id': audience_member_id},
                            {'$set': {'finished_once': True}}
                        )

            except tweepy.TweepError as twperr:
                print(twperr) # in case of errors due to protected accounts
                pass

            print("Processed " + str(page_count) + " page(s).")

            Connection.Instance().audience_networks_DB['all_audience_members'].update(
                { 'id': audience_member_id },
                { '$set':{'last_processed': datetime.now(), # update last processed time of this audience member
                        'last_followers_count': audience_member['last_followers_count']+ followers_count}
                }
            )

            print("Processed audience_member: " + str(audience_member_id) + " : " + str(followers_count) + " new followers." ) # Processing DONE.
            print("========================================")
            audience_member_count +=1


def main():
    get_followers_of_all_audience_members(5000,20000)

    #construct_all_audience_members()
    return
    if (len(sys.argv) >= 2):

        locations = ['italy'] # relevant locations
        #locations.append('slovakia')
        #locations.append('spain')
        #locations.append('uk')

        print("Script ran: " + str(datetime.now()))

        with Connection.Instance().get_cursor() as cur:
            sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            )
            cur.execute(sql)
            topics = cur.fetchall() # list of all topics

        for topicID,topicName in topics:
            if topicID == 24 or topicID == 25 or topicID ==26 or topicID ==27:
                continue
            for location in locations:
                print("================================================================================================")
                print("Getting audience network...  " + ", TOPIC: " + topicName + "(" + str(topicID) + ")" +  " , LOCATION: " + location )
                get_audience_network(topicID=topicID, location=location)
    else:
        print("Usage: python get_audience_network.py <server_ip>")

if __name__ == "__main__":
    main()
