import time  # for debug

import numpy as np
import pymongo  # for pymongo functions
import tweepy  # Twitter API helper package
from tweepy import OAuthHandler

from application.Connections import Connection

consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P"  # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7"  # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

GET_PROFILE_RATE_LIMIT = 100


def get_user_profile(unprocessed_user_ids, topicID):
    '''
    gets the profiles 100 at a time for the given user id list and topic.
    '''
    users = []
    try:
        users = api.lookup_users(unprocessed_user_ids)  # (!) max size limit of user_ids = 100
    except tweepy.TweepError as twperr:
        # it means the user account has been suspended, protected or closed.
        # we can also delete it from the user ids list in the database if we like.
        print(twperr)
        pass

    for i in range(len(users)):
        users[i] = users[i]._json
        users[i]['topics'] = [topicID]

    # add the users to the all audience collection
    try:
        Connection.Instance().audienceDB['all_audience'].insert_many(users, ordered=False)
    except:
        print("Exception in insert_many.")

    # mark the users as processed and add their location info.
    operations = []
    for user in users:
        operations.append(
            pymongo.UpdateOne(
                {'id': user['id']},
                {'$set':
                     {'location': user['location'],
                      'processed': True
                      }
                 })
        )

    # max size of operations will be 100 (rate limit).
    if len(operations) != 0:
        Connection.Instance().audienceDB[str(topicID)].bulk_write(operations, ordered=False)

    print("Processed " + str(len(unprocessed_user_ids)) + " users.")


def get_all_user_profiles_by_topic(topicID):
    start = time.time()
    print("============================================")
    print("Getting user profiles for topic: " + str(topicID))
    print("Finding already processed profiles...")
    # find user IDS whose profiles have been processed for this topic
    # if the list is too big (millions), we need to optimize this part in terms of memory. Do it batch by batch.
    # BATCH_SIZE = 20000

    userID_list_unprocessed_for_current_topic = []
    # if the list size exceeds 16MB, mongo will raise an error. In that case, append one by one using a cursor.
    try:
        userID_list_unprocessed_for_current_topic = Connection.Instance().audienceDB[str(topicID)].distinct('id', {
            'processed': False})
    except:
        print("Size of the unprocessed audience list for current topic exceeds 16MB. Appending one by one.")
        for userProfile in Connection.Instance().audienceDB[str(topicID)].find({'processed': False}, {'id': 1}):
            userID_list_unprocessed_for_current_topic.append(userProfile['id'])
    print("Unprocessed user ids for current topic found in " + str(time.time() - start) + " seconds.")
    start = time.time()

    if len(userID_list_unprocessed_for_current_topic) == 0: return

    processed_userID_list = []
    # processed user ids refer to those who have not been processed for this topic but processed before for another topic aka. in all_audience.

    try:
        for processedProfile in Connection.Instance().audienceDB[str(topicID)].find(
                {'id': {'$in': Connection.Instance().audienceDB['all_audience'].distinct('id')}, 'processed': False},
                {'id': 1}):
            processed_userID_list.append(processedProfile['id'])
    except:
        print("All_audience size exceeds 16MB. Finding processed profiles could be a little slow. ")
        pipeline = [
            # {'$unwind':...},
            {'$match': {'processed': False}},
            {'$lookup': {
                'from': 'all_audience',
                'localField': 'id',
                'foreignField': 'id',
                'as': 'in_all_audience'
            }},
            # {'$group': ...},
            {'$match': {'in_all_audience': {'$ne': []}}},
            # if the user is in all_audience, this list will include his user id (otherwise, it will be empty)
            {'$project': {'id': 1}}
        ]
        cursor = Connection.Instance().audienceDB[str(topicID)].aggregate(pipeline)
        print("Aggregation complete in " + str(time.time() - start) + " seconds")
        start = time.time()
        for processedProfile in cursor:
            processed_userID_list.append(processedProfile['id'])
        print("Insertion complete in " + str(
            time.time() - start) + " seconds. Already processed users list length:" + str(len(processed_userID_list)))

    print("# of unprocessed ids for current topic: " + str(len(userID_list_unprocessed_for_current_topic)))
    print("# of ids already in all_audience: " + str(len(processed_userID_list)))

    # set difference: userID_list - processed_userID_list
    unprocessed_userID_list = [userID for userID in userID_list_unprocessed_for_current_topic if
                               userID not in processed_userID_list]
    len_unprocessed_userID_list = len(unprocessed_userID_list)

    print("# of ids to be processed now: " + str(len_unprocessed_userID_list))

    # Process users that are being added to the audience for the first time batch by batch
    batch_size = GET_PROFILE_RATE_LIMIT
    no_batches = int(np.ceil(len_unprocessed_userID_list / batch_size))
    print("Number of batches to process: " + str(no_batches))

    for i in range(no_batches):
        print("Processing batch " + str(i))
        current_batch_size = min(batch_size, len_unprocessed_userID_list - i * batch_size)
        batch = unprocessed_userID_list[:current_batch_size]
        get_user_profile(batch, topicID)
        del unprocessed_userID_list[:current_batch_size]  # delete the already processed users

    # if the user has been added to the audience before, update.
    print("Updating user topics lists...")
    Connection.Instance().audienceDB['all_audience'].update(
        {'id': {'$in': processed_userID_list}},
        {'$addToSet': {'topics': topicID}},  # add current topic to the user's topics list
        multi=True
    )

    start = time.time()
    operations = []
    batch_count = 0
    # These users have been processed before in another topic.
    # mark them users as processed and add their location info.
    print("Marking the users that have already been processed in another topic...")

    processedProfiles = list(
        Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': processed_userID_list}},
                                                              {'id': 1, 'location': 1}))
    for processedProfile in processedProfiles:
        operations.append(
            pymongo.UpdateOne(
                {'id': processedProfile['id']},
                {'$set':
                     {'location': processedProfile['location'],
                      'processed': True
                      }
                 })
        )
        # Send once every 1000 in batch
        if (len(operations) == 1000 or (
                batch_count == int(np.ceil(len(processedProfiles) / 1000)) - 1 and len(operations) == len(
                processedProfiles) - batch_count * 1000)):
            batch_count += 1
            Connection.Instance().audienceDB[str(topicID)].bulk_write(operations, ordered=False)
            operations = []

    print(time.time() - start)


def main():
    '''
    # For a single topic
    if (len(sys.argv) >= 2):
        # user profiles should be unique
        Connection.Instance().audienceDB['all_audience'].create_index("id",unique=True)
        get_all_user_profiles_by_topic(topicID=int(sys.argv[2]))
    else:
    	print("Usage: python get_user_profiles.py <server_ip> <topicID>")
    '''
    # For all topics
    Connection.Instance().audienceDB['all_audience'].create_index("id", unique=True)
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM topics "
        )
        cur.execute(sql)
        topics = cur.fetchall()  # list of all topics
        while (1):
            for topic in topics:
                get_all_user_profiles_by_topic(topicID=topic[0])
            time.sleep(3)


if __name__ == "__main__":
    main()

# idlerden profiller i al, islendi islenmedi fieldi ekle, profil alirken islenmisse sadece topic listesine ekle.
# user profillerden olusan kocaman bir collection olacak.
# profile alirken lokasyonu id listesine field olarak ekle.
# daha sonra sample cekerken idlerden findla profilleri cek (id $in [id_list])

# processed index? locationu degisirse sorun olusur.
