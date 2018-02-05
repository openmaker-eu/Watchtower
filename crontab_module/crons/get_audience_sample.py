# Author: Kemal Berk Kocabagli

import datetime
import sys
import time  # for debug
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))
import numpy as np  # for sampling

from predict_location.predictor import Predictor  # for location

from application.Connections import Connection


def print_sample_audience(sample_audience_weighted, sample_audience_exploration):
    print('{:>1}{:>20}{:>40}{:>20}'.format("", "Screen name", "Location", "Followers count, Influencers count"))
    count1 = 1
    for i in range(len(sample_audience_weighted)):
        user = sample_audience_weighted[i]
        # print(str(count1) + " - " + user['screen_name'] + "," + user['location'] + " ," + str(user['followers_count']))
        print(
            '{}{:>20}{:>40}{:>20}{:>20}'.format(count1, user['screen_name'], user['location'], user['followers_count'],
                                                user['influencers_count']))
        count1 += 1
    count2 = 1
    print("\nExploration:")
    for i in range(len(sample_audience_exploration)):
        user = sample_audience_exploration[i]
        print(
            '{}{:>20}{:>40}{:>20}{:>20}'.format(count2, user['screen_name'], user['location'], user['followers_count'],
                                                user['influencers_count']))
        count2 += 1


# gets a sample from the audience for a given topic
# applies location filtering first
def get_audience_sample_by_topic(userID, topicID, location, sample_size, signal_strength):
    start = time.time()
    location = location.lower()  # cast location to lowercase
    loc_filtered_audience_ids = []

    # filter audience by location
    if (location.lower() == 'global'): # do not filter by a specific location.
        try:
            loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id', {'processed':True,'location':{'$ne':''},'$where': 'this.influencers.length > ' + str(signal_strength)})
        except:
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'processed':True,'location':{'$ne':''},'$where': 'this.influencers.length > '+ str(signal_strength)},{'_id':0,'id':1}):
                loc_filtered_audience_ids.append(audience_member['id'])
    else:
        location_predictor = Predictor()
        location = location_predictor.predict_location(location)
        if 'predicted_location' not in dumps(Connection.Instance().audienceDB[str(topicID)].find({}).sort([('_id',-1)]).limit(1)):
            print("Using regex for location...")
            regx = location_regex.getLocationRegex(location)
            loc_filtered_audience_ids = []
            try:
                loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id', {'location': {'$regex':regx}})
            except:
                for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'location': regx}, {'id': 1}):
                    loc_filtered_audience_ids.append(audience_member['id'])
        else:
            print("Using predictions for location...")
        # if 'predicted_location' not in dumps(Connection.Instance().audienceDB[str(topicID)].find({}).sort([('_id',-1)]).limit(1)):
        #     print("running predict location...")
        #     # call predicted_location function on current topic
        #     findPredictedLocation(Connection.Instance().machine_host, str(topicID), Connection.Instance().audienceDB, "location", location_predictor)
            try:
                loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topicID)].distinct('id',{'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)})
            except:
                for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)},{'_id':0,'id':1}):
                    loc_filtered_audience_ids.append(audience_member['id'])

    print("Filtered audience by location in " + str(time.time() - start) + " seconds.")
    start = time.time()

    audience = list(Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': loc_filtered_audience_ids}}))

    # method 1
    followers_counts = np.asarray([user['followers_count'] for user in audience])
    # method 2
    influencer_counts = np.asarray([len(user['influencers']) for user in list(
        Connection.Instance().audienceDB[str(topicID)].find({'id': {'$in': loc_filtered_audience_ids}}))])

    for i in range(len(audience)):
        audience[i]['influencers_count'] = int(influencer_counts[i])

    audience_size = len(loc_filtered_audience_ids)
    print("Audience size after location filtering: " + str(audience_size))
    if (audience_size == 0):
        print("No audience to be sampled.")
    else:
        size = min(sample_size,audience_size)
        ### ! Normally, we will use userID to carry out this sampling. it will be personalized!

        # Sample
        # 80% of the audience from a distribution weighed by number of influencers followed within the topic
        # 20% of the audience from a uniformly random distribution
        weighed_distribution_sample_size = int(0.8 * size)
        uniform_distribution_sample_size = size - weighed_distribution_sample_size
        print(str(len(audience)))
        print(str(len(influencer_counts)))
        try:
            sample_audience_weighted = np.random.choice(audience, size=weighed_distribution_sample_size, replace=False,
                                                        p=(influencer_counts ** 2) / sum(influencer_counts ** 2))
        except:
            print("The list lengths were not equal. Topic: " + str(topicID) + " , location: " + location + ". Sampling uniformly...")
            sample_audience_weighted = np.random.choice(audience, size=weighed_distribution_sample_size,
                                                       replace=False)

        # deterministic, sorted by influencers count.
        # sample_audience_weighted = sorted(audience, key=lambda x: x['influencers_count'], reverse=True)[0:weighed_distribution_sample_size]
        audience_left = [user for user in audience if user not in sample_audience_weighted]
        sample_audience_exploration = np.random.choice(audience_left, size=uniform_distribution_sample_size,
                                                   replace=False)
        print("Finished sampling in " + str(time.time() - start) + " seconds.")

        sample_audience = []
        for user in sample_audience_weighted:
            user['sample_type'] = 'weighted'
            sample_audience.append(user)
        for user in sample_audience_exploration:
            user['sample_type'] = 'exploration'
            sample_audience.append(user)

        print("Saving to MongoDB...")

        if (userID == -1):  # independent of the user - location based only.
            Connection.Instance().audience_samples_DB[str(location) + "_" + str(topicID)].drop()
            try:
                Connection.Instance().audience_samples_DB[str(location) + "_" + str(topicID)].insert_many(
                    sample_audience)
            except Exception as e:
                print("Exception in insert_many:" + str(e))
        else:
            # save the sample audience to MongoDB
            Connection.Instance().audience_samples_DB[str(userID) + "_" + str(topicID)].drop()
            try:
                Connection.Instance().audience_samples_DB[str(userID) + "_" + str(topicID)].insert_many(sample_audience)
            except Exception as e:
                print("Exception in insert_many:" + str(e))
                # print_sample_audience(sample_audience_weighted, sample_audience_exploration)


# find and store audience samples for all users, for all of their topics.
def main():
    if (len(sys.argv) >= 4):

        location = sys.argv[1]  # get location from commandline.
        getForAllLocations = sys.argv[2]  # should the sampling be done for all relevant locations
        N = 500  # audience sample size
        signal_strength = 3

        print("Script ran: " + str(datetime.datetime.now()))

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id, topic_name "
                "FROM topics "
            )
            cur.execute(sql)
            topics = cur.fetchall()  # list of all topics
            topic_dict = dict()
            for topicID, topicName in topics:
                topic_dict[topicID] = topicName

            sql = (
                "SELECT user_id, topic_id "
                "FROM user_topic "
            )
            cur.execute(sql)
            users_and_topics = cur.fetchall()  # list of all topics

        # for userID, topicID in users_and_topics:
        #     print("================================================================================================")
        #     print("Sampling audience for USER: " + str(userID) + " , LOCATION: " + location + ", TOPIC: " + topic_dict[
        #         topicID] + "(" + str(topicID) + ")")
        #     get_audience_sample_by_topic(userID=userID, topicID=topicID, location=location, sample_size=N, signal_strength=signal_strength)

        if (getForAllLocations == "0"):
            return

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT location_name, location_code "
                "FROM relevant_locations "
            )
            cur.execute(sql)
            location_dict = dict()
            for location_name, location_code in cur.fetchall():
                location_dict[location_code] = location_name

        for topicID, topicName in topics:
            for loc in list(location_dict.keys()):
                print("Sampling audience for LOCATION: " + location_dict[loc] + ", TOPIC: " + topicName + "(" + str(topicID) + ")")
                get_audience_sample_by_topic(userID=-1, topicID=topicID, location=loc, sample_size=N, signal_strength=signal_strength)

    else:
        print("Usage: python get_audience_sample.py <server_ip> <location> <fetch_for_all_relevant_locations>")


if __name__ == "__main__":
    main()
