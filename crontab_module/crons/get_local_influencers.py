# Author: Kemal Berk Kocabagli

import sys  # to get system arguments
import time  # for debug
from datetime import \
    datetime  # to print the date & time in the output log whenever this script is run OR for time related checks

sys.path.insert(0,'/root/cloud')
sys.path.insert(0,'/root/.local/share/virtualenvs/cloud-rP5jkfQF/lib/python3.5/site-packages/')

from predict_location.predictor import Predictor  # for location

from application.Connections import Connection


# gets the local influencers for a given topic and location
def get_local_influencers_by_topic(topicID, location, size, signal_strength=5, FOLLOWING_LIMIT=20000):
    location = location.lower()
    if location == "global":
        return

    location_predictor = Predictor()
    location = location_predictor.predict_location(location)
    # at this point location is a country code
    start = time.time()
    # filter audience by location
    # get location of the user from postgre.
    loc_filtered_audience_ids = []

    # if 'predicted_location' not in dumps(Connection.Instance().audienceDB[str(topicID)].find({}).sort([('_id',-1)]).limit(1)):
    #     print("running predict location...")
    #     # call predicted_location function on current topic
    #     findPredictedLocation(Connection.Instance().machine_host, str(topicID), Connection.Instance().audienceDB, "location", location_predictor)
    if 'predicted_location' not in dumps(Connection.Instance().audienceDB[str(topicID)].find({}).sort([('_id',-1)]).limit(1)):
        print("Using regex for location...")
        regx = getLocationRegex(location)
        loc_filtered_audience_ids = []
        try:
            loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id', {'location': {'$regex':regx}})
        except:
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location': regx}, {'id': 1}):
                loc_filtered_audience_ids.append(audience_member['id'])
    else:
        print("Using predictions for location...")
        try:
            loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id',{'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)})
        except:
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)},{'_id':0,'id':1}):
                loc_filtered_audience_ids.append(audience_member['id'])

    print("Filtered audience in " + str(time.time()-start) + " seconds. Audience size: " +str(len(loc_filtered_audience_ids)) )
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
    print("LOCATION:" + location)

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
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT location_name, location_code "
                "FROM relevant_locations "
            )
            cur.execute(sql)
            location_dict = dict()
            for location_name, location_code in cur.fetchall():
                location_dict[location_code] = location_name

        locations = list(location_dict.keys()) # relevant locations
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
