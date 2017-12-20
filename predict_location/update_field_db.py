from predictor import Predictor
import pymongo
import time
from pdb import set_trace
###
LOC_DATABASE_PATH = "city_location.txt"
COUNTRY_DATABASE_PATH = "country_code.txt"
MONGO_USERNAME_PASS = 'mongodb://admin:smio1EUp@'
MONGO_PORT = ':27017/'
###

def update_field_db(host, database_name, field_name):
    # Connect to server
    mongoDBClient = pymongo.MongoClient(MONGO_USERNAME_PASS+host+MONGO_PORT, connect=False)

    if database_name not in mongoDBClient.database_names():
        raise Exception("Database does not exist !")

    database = mongoDBClient.get_database(database_name)

    # Create predictor object
    predictor = Predictor(LOC_DATABASE_PATH, COUNTRY_DATABASE_PATH)

    # Which collections to pass
    exclude = ["all_audience"]

    # Get names of all collections in the database
    collection_names = database.collection_names()

    # Set the update field
    update_field_name = "predicted_" + field_name

    for collection_name in collection_names:
        if collection_name in include:
            print("Now processing collection :", collection_name)

            collection = database.get_collection(collection_name)
            bulk = collection.initialize_ordered_bulk_op()
        
            t_start = time.time()        

            for record in collection.find():
                if field_name in record:
                    bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : predictor.predict_location(record[field_name])}})
                else:
                    bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : ""}})

            try:
                bulk.execute()
                t_end = time.time()
                print("     It took {} seconds ...".format(t_end - t_start))
            except pymongo.errors.InvalidOperation:
                print("     NO RECORD WITH {} FIELD".format(field_name.upper()))
