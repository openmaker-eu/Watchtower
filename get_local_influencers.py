# Author: Kemal Berk Kocabagli

import sys # to get system arguments
import time # for debug
import re # for regex in location filtering
import pymongo # for pymongo functions
import numpy as np # for sampling
from datetime import datetime # to print the date & time in the output log whenever this script is run OR for time related checks
from location_regex import *

from application.Connections import Connection

# gets the local influencers for a given topic and location
def get_local_influencers_by_topic(topicID, location, size,signal_strength=5, FOLLOWING_LIMIT=20000):
    start = time.time()
    # filter audience by location
    # get location of the user from postgre.
    regx = getLocationRegex(location)
    loc_filtered_audience_ids = []
    try:
        loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id',{'location':regx, '$where':'this.influencers.length > ' + str(signal_strength)})
    except:
        for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location':regx, '$where':'this.influencers.length > ' + str(signal_strength)},{'_id':0,'id':1}):
            loc_filtered_audience_ids.append(audience_member['id'])

    print("Filtered audience in " + str(time.time()-start) + " seconds.")
    start = time.time()

    audience = Connection.Instance().audienceDB['all_audience'].aggregate(
    [
        {'$match': {'id':{'$in':loc_filtered_audience_ids}, 'friends_count':{'$lt':FOLLOWING_LIMIT}}},
        {'$project': {'_id': 0}},
        {'$sort': {'followers_count':-1}}
    ],
    allowDiskUse= True
    )

    audience = list(audience)
    local_influencers = audience[:size]

    print("Saving to MongoDB...")
    # save the sample audience to MongoDB
    Connection.Instance().local_influencers_DB[str(topicID)+"_"+str(location)].drop()
    try:
            Connection.Instance().local_influencers_DB[str(topicID)+"_"+str(location)].insert_many(local_influencers)
    except Exception as e:
        print("Exception in insert_many:" + str(e))

# find and store local influencers for relevant locations for all of the topics.
def main():
    if (len(sys.argv) >= 2):

        locations = ['italy','slovakia','spain','uk'] # relevant locations
        N = 20 # local influencers size
        signal_strength = 5
        FOLLOWING_LIMIT = 20000

        print("Script ran: " + str(datetime.now()))

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
                print("Getting local influencers...  " + " , LOCATION: " + location + ", TOPIC: " + topicName + "(" + str(topicID) + ")")
                get_local_influencers_by_topic(topicID=topicID, location=location, size=N, signal_strength=signal_strength)
    else:
        print("Usage: python get_local_influencers.py <server_ip>")

if __name__ == "__main__":
    main()
