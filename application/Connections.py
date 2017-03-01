import pymongo
import psycopg2
from utils.Singleton import Singleton

@Singleton
class Connection:
    MongoDBClient = None
    db = None # MongoDB
    PostGreSQLConnect = None
    cur = None # PostgreSQL

    def __init__(self):
        try:
            self.MongoDBClient = pymongo.MongoClient('mongodb://admin:smio1EUp@localhost:27017/')
            self.db = self.MongoDBClient.openMakerdB
            self.PostGreSQLConnect = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='smio#1EUp'")
            self.cur = self.PostGreSQLConnect.cursor()
            print "new connection"
        except Exception as e:
            print e
            print "I am unable to connect to the database"
