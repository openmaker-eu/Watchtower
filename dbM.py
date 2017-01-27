import pymongo
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

def connection_try():
    try:
        c = MongoClient(host="138.68.92.181", port=27017)
        #return "Connected successfully"
        return c
    except ConnectionFailure, e:
        sys.stderr.write("Could not connect to MongoDB: %s" % e)
        sys.exit(1)

def handle_db(client,db_name):
    dbh = client[db_name]
    assert dbh.client == client
    #print "Successfully set up a database handle"
    return dbh
