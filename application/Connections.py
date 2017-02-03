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
            self.MongoDBClient = pymongo.MongoClient('138.68.92.181', 27017)
            self.db = self.MongoDBClient.openMakerdB
            self.PostGreSQLConnect = psycopg2.connect("dbname='postgres' user='postgres' host='138.68.92.181' port='5432' password='a'")
            self.cur = self.PostGreSQLConnect.cursor()
            print "new connection"
        except Exception as e:
            print e
            print "I am unable to connect to the database"
