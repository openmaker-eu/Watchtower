# Author: Kemal Berk Kocabagli
import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))
sys.path.insert(0, './')

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
def get_audience_sample_by_topic(topic_id, locations, sample_size, signal_strength, predictor):
    start = time.time()
    print("Sampling audiences for topic: " + str(topic_dict[topic_id]))
    # First, filter by signal strength
    print("Passing followers from signal strength filter...")
    passed_signal_strength = []
    try:
        passed_signal_strength = Connection.Instance().audienceDB[str(topic_id)].distinct(
            'id',
            {'processed': True,
            '$where': 'this.influencers.length > ' + str(signal_strength)
            }
        )
    except:
        for audience_member in Connection.Instance().audienceDB[str(topic_id)].find(
                {'processed': True, '$where': 'this.influencers.length > ' + str(signal_strength)}, {'_id': 0, 'id': 1}):
            passed_signal_strength.append(audience_member['id'])
    print("Done in " + str(time.time() - start) + " seconds. Going on to location filtering and sampling...")

    # Then, iterate over all relevant locations and sample.
    for location in list(location_dict.keys()):
        print("Sampling audience for LOCATION: " + location_dict[location] + "(" + location + "), "
            "TOPIC: " + topic_dict[topic_id] + "(" + str(topic_id) + ")")
        if (topic_id, location) in aud_exec_dict:
            # print(str((datetime.datetime.utcnow() - aud_exec_dict[(topicID, loc)]).seconds))
            if (datetime.datetime.utcnow() - aud_exec_dict[(topic_id, location)]).seconds < (int(hours) * 60 * 60):
                print("Skipping audience since it has been sampled within the last " + str(hours) + " hour(s).")
                continue
        start_ts = datetime.datetime.utcnow()
        start = time.time()
    # ====================================================================================
        location = location.lower()  # cast location to lowercase
        loc_filtered_audience_ids = []

        # filter audience by location
        if location == 'global':  # do not filter by a specific location.
            try:
                loc_filtered_audience_ids = Connection.Instance().audienceDB[str(topic_id)].distinct('id', {
                    'id': {'$in': passed_signal_strength},
                    'location': {'$ne': ''}
                })
            except:
                for audience_member in Connection.Instance().audienceDB[str(topic_id)].find(
                        {'id': {'$in': passed_signal_strength},
                         'location': {'$ne': ''}}, {'_id': 0, 'id': 1}):
                    loc_filtered_audience_ids.append(audience_member['id'])
        else:  # filter by location then sample.
            predicted_location_count = 0
            location_predictor = predictor
            location = location_predictor.predict_location(location)
            loc_filtered_audience_ids = set()

            # use predicted_location
            try:
                loc_filtered_audience_ids.add(Connection.Instance().audienceDB[str(topic_id)].distinct('id', {
                    'id': {'$in': passed_signal_strength},
                    'predicted_location': {'$exists': True},
                    'predicted_location': location}))
            except:
                for audience_member in Connection.Instance().audienceDB[str(topic_id)].find({
                        'id': {'$in': passed_signal_strength},
                        'predicted_location': {'$exists': True},
                        'predicted_location': location},
                        {'_id': 0, 'id': 1}):
                    loc_filtered_audience_ids.add(audience_member['id'])

            predicted_location_count = len(loc_filtered_audience_ids)
            print("Filtered " + str(
                predicted_location_count) + " audience members according to predicted location in " + str(
                time.time() - start) + " seconds.")
            start = time.time()
            regx = location_regex.getLocationRegex(location)

            # use regex on location
            try:
                loc_filtered_audience_ids.add(Connection.Instance().audienceDB[str(topic_id)].distinct('id', {
                    'id': {'$in': passed_signal_strength},
                    'predicted_location': {'$exists': False},
                    'location': {'$regex': regx}}))
            except:
                for audience_member in Connection.Instance().audienceDB[str(topic_id)].find({
                    'id': {'$in': passed_signal_strength},
                    'predicted_location': {'$exists': False},
                    'location': regx},
                    {'_id': 0, 'id': 1}):
                    loc_filtered_audience_ids.add(audience_member['id'])

            loc_filtered_audience_ids = list(loc_filtered_audience_ids)
            regex_count = len(loc_filtered_audience_ids) - predicted_location_count
            print("Filtered " + str(regex_count) + " audience members with regex in " + str(
                time.time() - start) + " seconds.")
            start = time.time()

        print("Filtered audience by location in " + str(time.time() - start) + " seconds.")
        start = time.time()

        # GET THE AUDIENCE TWITTER PROFILES
        audience = list(
            Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': loc_filtered_audience_ids}}))

        # method 1
        followers_counts = np.asarray([user['followers_count'] for user in audience])
        # method 2
        influencer_counts = np.asarray([len(user['influencers']) for user in list(
            Connection.Instance().audienceDB[str(topic_id)].find({'id': {'$in': loc_filtered_audience_ids}}))])

        for i in range(len(audience)):
            audience[i]['influencers_count'] = int(influencer_counts[i])

        audience_size = len(loc_filtered_audience_ids)
        print("Audience size after location filtering: " + str(audience_size))
        if audience_size == 0:
            print("No audience to be sampled.")
        else:
            size = min(sample_size, audience_size)
            ### ! Normally, we will use userID to carry out this sampling. it will be personalized!

            # Sample
            # 80% of the audience from a distribution weighed by number of influencers followed within the topic
            # 20% of the audience from a uniformly random distribution
            weighed_distribution_sample_size = int(0.8 * size)
            uniform_distribution_sample_size = size - weighed_distribution_sample_size
            print(str(len(audience)))
            print(str(len(influencer_counts)))
            try:
                sample_audience_weighted = np.random.choice(audience, size=weighed_distribution_sample_size,
                                                            replace=False,
                                                            p=(influencer_counts ** 2) / sum(influencer_counts ** 2))
            except:
                print("The list lengths were not equal. Topic: " + str(
                    topic_id) + " , location: " + location + ". Sampling uniformly...")
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

            # save the sample audience to MongoDB
            Connection.Instance().audience_samples_DB[str(location) + "_" + str(topic_id)].drop()
            try:
                Connection.Instance().audience_samples_DB[str(location) + "_" + str(topic_id)].insert_many(
                    sample_audience)
            except Exception as e:
                print("Exception in insert_many:" + str(e))

            # print_sample_audience(sample_audience_weighted, sample_audience_exploration)
    # ====================================================================================

            # save stats to POSTGRES
            end_ts = datetime.datetime.utcnow()

            sql = (
                "INSERT INTO audience_samples_last_executed "
                "VALUES (%(topicID)s, %(location)s, %(execution_duration)s, %(last_executed)s, %(from_predicted_location)s, %(from_regex)s) "
                "ON CONFLICT (topic_id,location) DO UPDATE "
                "SET execution_duration=%(execution_duration)s, last_executed=%(last_executed)s, from_predicted_location = %(from_predicted_location)s, from_regex = %(from_regex)s "
            )

            params = {
                'topicID': int(topic_id),
                'location': location,
                'execution_duration': end_ts - start_ts,
                'last_executed': end_ts,
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

def prepare_dictionaries():
    with Connection.Instance().get_cursor() as cur:
        # GET TOPICS
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            "WHERE is_masked_location = %s"
        )
        cur.execute(sql, [False])
        topics = cur.fetchall()  # list of all topics
        for topicID, topicName in topics:
            topic_dict[topicID] = topicName

        # GET RELEVANT LOCATIONS
        sql = (
            "SELECT location_name, location_code "
            "FROM relevant_locations "
        )
        cur.execute(sql)
        for location_name, location_code in cur.fetchall():
            location_dict[location_code] = location_name

        # GET LAST EXECUTION STATS FOR EACH AUDIENCE SAMPLE
        sql = (
            "SELECT topic_id, location, last_executed "
            "FROM audience_samples_last_executed "
        )

        cur.execute(sql)
        for topic_id, location, last_executed in cur.fetchall():
            aud_exec_dict[(topic_id, location)] = last_executed


topic_dict = dict()
location_dict = dict()
aud_exec_dict = dict()
N = 500  # audience sample size
signal_strength = 3
location_predictor = Predictor()
hours = 1

# find and store audience samples for all users, for all of their topics.
def main():
    print("Script ran: " + str(datetime.datetime.utcnow()))
    prepare_dictionaries()  # prepare topic, location and execution stat dicts.

    for topic_id, topic_name in topic_dict.items():
        get_audience_sample_by_topic(topic_id=topic_id, locations=list(location_dict.keys()), sample_size=N, signal_strength=signal_strength, predictor=location_predictor)
if __name__ == "__main__":
    main()
