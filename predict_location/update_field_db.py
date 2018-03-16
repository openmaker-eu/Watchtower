import time
import pymongo
from decouple import config
from .predictor import Predictor
###
MONGO_USERNAME_PASS = 'mongodb://{0}:{1}@'.format(config("MONGODB_USER"), config("MONGODB_PASSWORD"))
MONGO_PORT = ':27017/'
BATCH_SIZE = 100000
###

# Update single collection in the given database
def update_field_collection(host, collection_name, database, field_name, predictor):
    print("Predict {} field in collection {} of the database {}".format(field_name, collection_name, database.name))

    # Set the update field
    update_field_name = "predicted_" + field_name

    collection = database.get_collection(collection_name)

    if collection_name == "all_audience":
        return

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
def update_field_db(host, database_name, field_name):
    # Connect to server
    mongoDBClient = pymongo.MongoClient(MONGO_USERNAME_PASS+host+MONGO_PORT, connect=False)

    if database_name not in mongoDBClient.database_names():
        raise Exception("Database does not exist !")

    database = mongoDBClient.get_database(database_name)

    # Which collections to pass
    exclude = ["all_audience"]

    # Get names of all collections in the database
    collection_names = database.collection_names()

    # Create predictor object
    predictor = Predictor()

    for collection_name in collection_names:
        update_field_collection(host, collection_name, database, field_name,predictor)
