import time
import sys
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))

from application.Connections import Connection
from pymongo import InsertOne


if __name__ == "__main__":
    # Loop over all collections in audience_sample and add id's to last_tweets
    ids = set()
    begin = time.time()
    existing_ids = set([x["id"] for x in Connection.Instance().MongoDBClient.last_tweets["tweets"].find({},{"id":1,"_id":0})])
    print("Adding id's to set")
    for collection_name in Connection.Instance().audience_samples_DB.collection_names():
        collection = Connection.Instance().audience_samples_DB[collection_name]
        for t in collection.find({}, {"id": 1, "_id": 0}):
            ids.add(t["id"])

    
    ids = ids - existing_ids
    
    requests = [InsertOne({"id": twitter_id, "processed_once": False,"last_processed": None, "tweets": None}) for twitter_id in ids]

    # Create collection with index, if it does not exist
    collection = Connection.Instance().MongoDBClient.last_tweets["tweets"]
    collection.create_index("id", unique=True)

    if requests:
        collection.bulk_write(requests, ordered=False)
    end = time.time()
    print("DONE! It took {} seconds. Added {} documents.".format(end - begin , len(requests)))
