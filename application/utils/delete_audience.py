from application.Connections import Connection
import sys
import time

influencerDB = Connection.Instance().influencerDB
audienceDB = Connection.Instance().audienceDB
localInfluencersDB = Connection.Instance().local_influencers_DB
audienceSamplesDB = Connection.Instance().audience_samples_DB
audienceNetworksDB = Connection.Instance().audience_networks_DB

def delete_influencers(topic_id):
    influencerDB['all_influencers'].update(
        {'id': {'$in':Connection.Instance().influencerDB[str(topic_id)].distinct('id')}},
        {'$pull':{'topics': int(topic_id)}},
        multi=True
    )
    print("Deleted the topic from topics.")
    result = influencerDB['all_influencers'].delete_many(
        {'$where':'this.topics.length<1'}
    )
    print("Deleted " + str(result.deleted_count) + " influencers from all_influencers.")

def delete_audience(topic_id):
    try:
        audienceDB['all_audience'].update(
            {'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')}},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    except:
        audienceDB['all_audience'].update(
            {},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )

    print("Deleted the topic from topics.")

    BATCH_SIZE = 50000
    cursor = Connection.Instance().audienceDB['all_audience'].find({'$where':'this.topics.length<1'}).limit(BATCH_SIZE)
    BATCH_NO = 1
    deleted_count = 0

    while cursor.count(with_limit_and_skip=True):
        print("...Processing batch " + str(BATCH_NO))
        bulk = Connection.Instance().audienceDB['all_audience'].initialize_unordered_bulk_op()
        d=0
        for record in cursor:
            bulk.find({'_id':record['_id']}).remove()
            d +=1
        try:
            bulk.execute()
            deleted_count += d
        except:
            print("Error in bulk execute.")

        cursor = Connection.Instance().audienceDB['all_audience'].find({'$where':'this.topics.length<1'}).skip(BATCH_NO*BATCH_SIZE).limit(BATCH_SIZE)
        BATCH_NO += 1

    print("Deleted " + str(deleted_count) + " audience members from all_audience.")


def delete_local_influencers(topic_id):
    cn = localInfluencersDB.collection_names()
    collections_to_drop = [c for c in cn if str(topic_id) in c]

    for collection in collections_to_drop:
        localInfluencersDB.drop[collection]

def delete_audience_samples(topic_id):
    cn = audienceSamplesDB.collection_names()
    collections_to_drop = [c for c in cn if "_" + str(topic_id) in c]

    for collection in collections_to_drop:
        audienceSamplesDB.drop[collection]

def delete_audience_members(topic_id):
    try:
        audienceNetworksDB['all_audience'].update(
            {'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')}},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    except:
        audienceNetworksDB['all_audience'].update({},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    print("Deleted the topic from topics.")

    try:
        result = audienceNetworksDB['all_audience'].delete_many(
            {
            'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')},
            '$where':'this.topics.length<1'
            }
        )
    except:
        result = audienceNetworksDB['all_audience'].delete_many(
            {'$where':'this.topics.length<1'}
        )

    print("Deleted " + str(result.deleted_count) + " audience members from all_audience_members.")

def main(topic_to_delete):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, topic_name "
            "FROM archived_topics "
            "WHERE audience_deleted=false "
        )
        cur.execute(sql)
        topics = cur.fetchall()  # list of all topics
        topic_ids=[]
        print('topic ID    topic name')
    for topic in topics:
        topic_ids.append(str(topic[0]))
        print(str(topic[0]) + " " + str(topic[1]))

    topic_to_delete = int(topic_to_delete)
    if topic_to_delete not in topic_ids:
        print("Audience already deleted.")
        return

    start = time.time()

    print("Deleting influencers...")
    delete_influencers(topic_to_delete)
    print("Complete in " + str(time.time()-start) + " seconds.")
    start = time.time()

    print("Deleting audience...")
    delete_audience(topic_to_delete)
    print("Complete in " + str(time.time()-start) + " seconds.")
    start = time.time()

    print("Deleting local influencers...")
    delete_local_influencers(topic_to_delete)
    print("Complete in " + str(time.time()-start) + " seconds.")
    start = time.time()

    print("Deleting audience samples...")
    delete_audience_samples(topic_to_delete)
    print("Complete in " + str(time.time()-start) + " seconds.")
    start = time.time()

    print("Deleting audience members...")
    delete_audience_members(topic_to_delete)
    print("Complete in " + str(time.time()-start) + " seconds.")
    start = time.time()

    sql = (
        "UPDATE archived_topics "
        "SET audience_deleted = %s "
        "WHERE topic_id = %s"
    )
    cur.execute(sql, [True, int(topic_to_delete)])
    print("Updated PostgreSQL DB.")
