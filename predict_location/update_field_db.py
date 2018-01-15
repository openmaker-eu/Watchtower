import time
###
MONGO_USERNAME_PASS = 'mongodb://admin:smio1EUp@'
MONGO_PORT = ':27017/'
BATCH_SIZE = 100000
###

# Update single collection in the given database
def update_field_collection(host, collection_name, database, field_name, predictor):
    print("Predict {} field in collection {} of the database {}".format(field_name, collection_name, database.name))

    # Set the update field
    update_field_name = "predicted_" + field_name

    collection = database.get_collection(collection_name)
    bulk = collection.initialize_unordered_bulk_op()

    cursor = collection.find({update_field_name : {"$exists" : False}}).limit(BATCH_SIZE)
    n = 1
    while cursor.count(with_limit_and_skip=True):
        print("...Processing batch " + str(n))
        for record in cursor:
            if update_field_name in record:
                continue
            elif field_name in record:
                bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : predictor.predict_location(record[field_name])}})
            else:
                bulk.find({'_id':record['_id']}).update({'$set' : {update_field_name : ""}})
        try:
            bulk.execute()
        except pymongo.errors.InvalidOperation:
            print("     NO RECORD WITH {} FIELD IN THIS BATCH".format(field_name.upper()))

        cursor = collection.find({update_field_name : {"$exists" : False}}).skip(n*BATCH_SIZE).limit(BATCH_SIZE)
        n += 1


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
    predictor = Predictor(LOC_DATABASE_PATH, COUNTRY_DATABASE_PATH)

    for collection_name in collection_names:
        update_field_collection(host, collection_name, database, field_name,predictor)
