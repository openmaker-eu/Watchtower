# Author: Kemal Berk Kocabagli

import sys
from datetime import datetime  # to print the date & time in the output log whenever this script is run OR for time related checks
from decouple import config
import pymongo
import tweepy  # Twitter API helper package
from decouple import config
from tweepy import OAuthHandler

sys.path.insert(0, config("ROOT_DIR"))

from application.Connections import Connection

# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def copy_follower_ids_to_new_topics(influencer):
    print("Checking for new topics...")
    topics = influencer['topics']
    if (len(topics) == 1):
        return

    first_topic_follower_id_count = Connection.Instance().audienceDB[str(influencer['topics'][0])].count(
        {'influencers': influencer['id']})

    new_topics = []
    for idx in range(1, len(topics)):
        topicID = topics[idx]
        if (Connection.Instance().audienceDB[str(topicID)].count(
                {'influencers': influencer['id']}) < first_topic_follower_id_count):
            new_topics.append(topicID)

    if len(new_topics) != 0:
        print("New topics added to the influencer: " + influencer['screen_name'])
        for topicID in new_topics:
            # for all topics that have been newly added to the infuencer,
            # insert all the follower ids to the table of that topic using the first topic of the influencer.
            print("Copying follower ids to topic: " + str(topicID))
            Connection.Instance().audienceDB[str(topicID)].create_index("id", unique=True)
            try:
                Connection.Instance().audienceDB[str(topicID)].insert_many(list(
                    Connection.Instance().audienceDB[str(influencer['topics'][0])].find(
                        {'influencers': influencer['id']})), ordered=False)
            except:
                print("Exception in insert_many.")
            try:
                Connection.Instance().influencerDB['all_influencers'].update({"id": influencer['id']},
                                                                             {'$inc': {'processed_topic_count': 1}})
                print("Incremented processed topic count.")
            except:
                print("Error in updating processed_topic_count.")


def get_follower_ids_by_influencer(influencer):
    """
    gets the follower ids for a specific influencer from Twitter and saves them to MongoDB for each of the influencer's topics.

    most recent followers are in page 0.
    Start from page 0 and go until we come across <THRESHOLD> follower ids successively that we already have in our DB retrieved from this influencer.

    for new topics, followers are copied from the first topic of the influencer.
    """
    print("Getting follower ids for influencer " + str(influencer['screen_name']))

    if (influencer['protected'] == True):
        print("The account of this influencer is protected at the moment.")
        return 0

    start_cursor = -1  # get all the follower ids page by page, starting from most recent follower (first page)
    # if an influencer has not been processed until the end once, start from last cursor.
    if 'finished_once' in influencer:
        if influencer['finished_once'] == False:
            if 'last_cursor' in influencer:
                start_cursor = influencer['last_cursor']

    print("Start cursor value: " + str(start_cursor))

    cursor = tweepy.Cursor(api.followers_ids, screen_name=influencer['screen_name'], cursor=start_cursor)
    last_cursor = start_cursor

    page_count = 0
    followers_count = 0
    STOP_FLAG = 0
    THRESHOLD = 10
    already_added_ids = []

    try:
        for page in cursor.pages():
            if (cursor.iterator.next_cursor != 0):
                last_cursor = cursor.iterator.next_cursor
                # pprint.pprint(api.rate_limit_status()['resources']['followers'])
            print("Page length: " + str(len(page)))

            # upsert many
            print("UPSERTING")
            operations = []
            for i in range(len(page)):
                follower_id = page[i]
                if influencer['finished_once'] == True:
                    if Connection.Instance().audienceDB[str(influencer['topics'][0])].count(
                            {"$and": [{"id": follower_id}, {"influencers": influencer['id']}]}) != 0:
                        already_added_ids.append(follower_id)
                        print("follower # " + str(i) + " was already added. Follower id: " + str(follower_id))
                    # uncomment if we want successive followers to be already added.
                    else:
                        already_added_ids = []
                        print("ALREADY ADDED IDS EMTPIED at follower # " + str(i) + " with follower id: " + str(
                            follower_id))
                        operations.append(
                            pymongo.UpdateOne(
                                {'id': follower_id},
                                {'$setOnInsert': {'processed': False},
                                 # if the follower already exists, do not touch the 'processed' field
                                 '$addToSet': {'influencers': influencer['id']}
                                 }, upsert=True)
                        )
                        followers_count += 1

                    if len(already_added_ids) == THRESHOLD:
                        STOP_FLAG = 1
                        break
                else:
                    operations.append(
                        pymongo.UpdateOne(
                            {'id': follower_id},
                            {'$setOnInsert': {'processed': False},
                             # if the follower already exists, do not touch the 'processed' field
                             '$addToSet': {'influencers': influencer['id']}
                             }, upsert=True)
                    )
                    followers_count += 1

            print("Saving audience gathered to topics of this influencer. # of updates: " + str(len(operations)))
            # print("first 10 opearations:")
            # print(operations[:10])
            for topicID in influencer['topics']:
                # add follower ids under each topicID collection in MongoDB
                # Follower ids should be unique within a topic collection
                Connection.Instance().audienceDB[str(topicID)].create_index("id", unique=True)
                # max size of operations will be 5000 (page size).
                try:
                    if (len(operations) != 0):
                        Connection.Instance().audienceDB[str(topicID)].bulk_write(operations, ordered=False)
                except Exception as e:
                    print("Exception in bulk_write:" + str(e))

            if STOP_FLAG == 1:
                page_count += 1
                print("Stopping at page " + str(page_count - 1))
                print("Followers that resulted in STOP: " + str(already_added_ids))
                break

            if influencer[
                'finished_once'] == False:  # if we haven't finished processing an influencer, we need to update the last cursor.
                Connection.Instance().influencerDB['all_influencers'].update(
                    {'id': influencer['id']},
                    {'$set': {'last_cursor': last_cursor}}  # update last cursor of this influencer
                )

            page_count += 1  # increment page count
            if cursor.iterator.next_cursor == 0:  # if true, we are at the end of the followers for this influencer.
                Connection.Instance().influencerDB['all_influencers'].update(
                    {'id': influencer['id']},
                    {'$set': {'finished_once': True}}
                )

    except tweepy.TweepError as twperr:
        print(twperr)  # in case of errors due to protected accounts
        pass

    print("Processed " + str(page_count) + " page(s).")

    Connection.Instance().influencerDB['all_influencers'].update(
        {'id': influencer['id']},
        {
            '$set': {
                'last_processed': datetime.now()  # update last processed time of this influencer
            },
            '$inc': {
                'retrieved_follower_id_count': followers_count  # update retrieved follower count of this influencer
            }
        }
    )

    print("Processed influencer: " + influencer['screen_name'] + " : " + str(
        followers_count) + " new followers.")  # Processing DONE.

    print("========================================")
    return 1


def get_follower_ids():
    """
    gets the follower ids for all topics. Will be run periodically.
    """

    INFLUENCER_COUNT = 0
    INFLUENCER_NUMBER = 0
    N = 1500
    FOLLOWERS_LIMIT = int(config("FOLLOWERS_LIMIT"))  # pass the influencers who have more followers than the limit

    # sort influencers from most to least recently retrieved
    influencers = list(
        Connection.Instance().influencerDB['all_influencers'].find({}).sort([('_id', pymongo.DESCENDING)])
        # Connection.Instance().influencerDB['all_influencers'].find({}).sort([('_id', pymongo.ASCENDING)])
    )

    for influencer in influencers:
        # print("\nLooking at influencer no " + str(len(influencers) - INFLUENCER_NUMBER) + ":" + influencer['screen_name'])
        INFLUENCER_NUMBER += 1
        print("\nLooking at influencer no " + str(INFLUENCER_NUMBER) + ":" + influencer['screen_name'])
        copy_follower_ids_to_new_topics(influencer)
        if influencer['followers_count'] > FOLLOWERS_LIMIT:
            print("Passing this influencer as his followers count exceeds the limit.")
            continue
        # if the influencer has been processed before, wait for at least a day to process him again.
        # get_influencers will be run once per week. Therefore, no new topic can be added
        # to the influencer throughout a day.
        if 'last_processed' in influencer:
            if 'finished_once' in influencer:
                if influencer['finished_once']:
                    if (datetime.today() - influencer['last_processed']).days > 10:
                        result = get_follower_ids_by_influencer(influencer)
                        if result == 1:
                            INFLUENCER_COUNT += 1  # successfully processed the influencer
                    else:
                        print(influencer['screen_name'] + "(finished once) HAS ALREADY BEEN PROCESSED IN LAST 10 DAYS.")
                else:
                    if (datetime.today() - influencer['last_processed']).days > 1:
                        result = get_follower_ids_by_influencer(influencer)
                        if result == 1:
                            INFLUENCER_COUNT += 1  # successfully processed the influencer
                    else:
                        print(influencer['screen_name'] + " HAS ALREADY BEEN PROCESSED TODAY.")
        else:
            result = get_follower_ids_by_influencer(influencer)
            if result == 1: INFLUENCER_COUNT += 1  # successfully processed the influencer
        if (INFLUENCER_COUNT == N): break


def main():
    get_follower_ids()


if __name__ == "__main__":
    main()
