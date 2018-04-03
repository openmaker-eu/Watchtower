import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))

from predict_location.predictor import Predictor  # for location
from application.Connections import Connection # for database connections

import time
import pymongo

def fetchTopics():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id,is_masked_location "
            "FROM topics "
            "WHERE topics.is_masked_location = false "
        )
        cur.execute(sql)
        
        return [x[0] for x in cur.fetchall()]

# Update single collection in the given database
def update_field_collection(collection_name, database, field_name, predictor):
    print("Predict {} field in collection {} of the database {}".format(field_name, collection_name, database.name))

    # Set the update field
    update_field_name = "predicted_" + field_name

    collection = database.get_collection(collection_name)

    cursor = collection.find({update_field_name : {"$exists" : False}})

    bulk = collection.initialize_unordered_bulk_op()

    if not cursor.count():
        print("...No record to update !")
    else:
        print("...Number of records to update :",cursor.count())
        for record in cursor:
            if update_field_name in record: # This is redundant ?
                continue
            elif field_name in record:
                bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : predictor.predict_location(record[field_name])}})
            else:
                bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : ""}})
        print("...Execute bulk write")
        try:
            bulk.execute()
        except pymongo.errors.InvalidOperation as e:
            print(str(e))
        else:
            print("...DONE!")


# Update all collections in the given database
def update_field_db(database_name, field_name):

    if database_name not in Connection.Instance().MongoDBClient.database_names():
        raise Exception("Database does not exist !")

    database = Connection.Instance().MongoDBClient.get_database(database_name)

    topics = fetchTopics()

    # Create predictor object
    predictor = Predictor()

    for topic_id in topics:
        update_field_collection(str(topic_id), database, field_name,predictor)
