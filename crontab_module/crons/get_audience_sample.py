# Author: Kemal Berk Kocabagli

import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))

from application.utils.basic import *
from predict_location.predictor import Predictor  # for location
from application.Connections import Connection # for database connections

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
def get_audience_sample_by_topic(userID, topicID, location, sample_size, signal_strength, predictor):
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

        predicted_location_count = 0
        regex_count = len(loc_filtered_audience_ids)
    else:
        location_predictor = predictor
        location = location_predictor.predict_location(location)
        loc_filtered_audience_ids = set()

        try:
            loc_filtered_audience_ids.add(Connection.Instance().audienceDB[str(topicID)].distinct('id',{'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)}))
        except:
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'predicted_location':{'$exists':True}, 'predicted_location':location, '$where':'this.influencers.length > ' + str(signal_strength)},{'_id':0,'id':1}):
                loc_filtered_audience_ids.add(audience_member['id'])

        predicted_location_count = len(loc_filtered_audience_ids)
        print("Filtered " + str(predicted_location_count) + " audience members according to predicted location.")

        regx = location_regex.getLocationRegex(location)

        try:
            loc_filtered_audience_ids.add(Connection.Instance().audienceDB[str(topicID)].distinct('id', {'predicted_location':{'$exists':False},'location': {'$regex':regx}}))
        except:
            for audience_member in Connection.Instance().audienceDB[str(topicID)].find({'predicted_location':{'$exists':False},'location': regx}, {'_id':0,'id': 1}):
                loc_filtered_audience_ids.add(audience_member['id'])

        loc_filtered_audience_ids = list(loc_filtered_audience_ids)
        regex_count = len(loc_filtered_audience_ids)-predicted_location_count
        print("Filtered " + str(regex_count) + " audience members with regex.")


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

        return (predicted_location_count, regex_count)

# find and store audience samples for all users, for all of their topics.
def main():
    location = config("LOCATION") # get location from env.
    getForSpecificUsers = config("SPECIFIC_USERS_AUD") # should we process samples for specific users
    getForAllLocations = config("ALL_LOCATIONS_AUD")  # should we process samples for all relevant locations
    N = 500  # audience sample size
    signal_strength = 3
    location_predictor = Predictor()
    hours = 1

    print("Script ran: " + str(datetime.datetime.utcnow()))

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            "WHERE is_masked_location = %s"
        )
        cur.execute(sql, [False])
        topics = cur.fetchall()  # list of all topics
        topic_dict = dict()
        for topicID, topicName in topics:
            topic_dict[topicID] = topicName

        ids = [i[0] for i in topics]
        sql = (
            "SELECT user_id, topic_id "
            "FROM user_topic "
            "WHERE topic_id IN %s"
        )
        cur.execute(sql, [tuple(ids)])
        users_and_topics = cur.fetchall()  # list of all topics

        if (getForSpecificUsers == "1"):
            for userID, topicID in users_and_topics:
                print("================================================================================================")
                print("Sampling audience for USER: " + str(userID) + " , LOCATION: " + location + ", TOPIC: " + topic_dict[
                    topicID] + "(" + str(topicID) + ")")
                get_audience_sample_by_topic(userID=userID, topicID=topicID, location=location, sample_size=N, signal_strength=signal_strength, predictor=location_predictor)

        if (getForAllLocations == "1"):
            sql = (
                "SELECT location_name, location_code "
                "FROM relevant_locations "
            )
            cur.execute(sql)
            location_dict = dict()
            for location_name, location_code in cur.fetchall():
                location_dict[location_code] = location_name

            sql = (
                "SELECT topic_id, location, last_executed "
                "FROM audience_samples_last_executed "
            )

            cur.execute(sql)
            aud_exec_dict= dict()
            for topic_id, location, last_executed in cur.fetchall():
                aud_exec_dict[(topic_id, location)] = last_executed

    for topicID, topicName in topics:
        for loc in list(location_dict.keys()):
            print("Sampling audience for LOCATION: " + location_dict[loc] + "(" + loc + "), TOPIC: " + topicName + "(" + str(topicID) + ")")
            if (topicID, loc) in aud_exec_dict:
                #print(str((datetime.datetime.utcnow() - aud_exec_dict[(topicID, loc)]).seconds))
                if ((datetime.datetime.utcnow() - aud_exec_dict[(topicID, loc)]).seconds < (int(hours) * 60*60)):
                    print("Skipping audience since it has been sampled within the last " + str(hours) + " hour(s).")
                    continue
            start = datetime.datetime.utcnow()
            result = get_audience_sample_by_topic(userID=-1, topicID=topicID, location=loc, sample_size=N, signal_strength=signal_strength, predictor=location_predictor)

            try:
                predicted_location_count, regex_count =result
            except:
                predicted_location_count, regex_count = (0,0)

            end = datetime.datetime.utcnow()

            sql = (
                "INSERT INTO audience_samples_last_executed "
                "VALUES (%(topicID)s, %(location)s, %(execution_duration)s, %(last_executed)s, %(from_predicted_location)s, %(from_regex)s) "
                "ON CONFLICT (topic_id,location) DO UPDATE "
                "SET execution_duration=%(execution_duration)s, last_executed=%(last_executed)s, from_predicted_location = %(from_predicted_location)s, from_regex = %(from_regex)s "
            )

            params = {
                'topicID': int(topicID),
                'location': loc,
                'execution_duration':end-start,
                'last_executed': end,
                'from_predicted_location': int(predicted_location_count),
                'from_regex': int(regex_count)
            }

            print("Writing logs to Postgres...")
            with Connection.Instance().get_cursor() as cur:
                try:
                    cur.execute(sql, params)
                except:
                    print("Error while saving.")
            print("Complete.\n")

if __name__ == "__main__":
    main()
