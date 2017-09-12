from __future__ import print_function

import psycopg2
import pymongo
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool

from application.utils.Singleton import Singleton


@Singleton
class Connection:
    def __init__(self):
        try:
            self.MongoDBClient = pymongo.MongoClient('mongodb://admin:smio1EUp@138.68.92.181:27017/', connect=False)
            self.db = self.MongoDBClient.openMakerdB
            self.newsdB = self.MongoDBClient.newsdB
            self.feedDB = self.MongoDBClient.feedDB
            self.conversations = self.MongoDBClient.conversations
            self.events = self.MongoDBClient.events
            self.hashtags = self.MongoDBClient.hashtags
            self.redditFacebookDB = self.MongoDBClient.redditFacebookDB
            self.newsPoolDB = self.MongoDBClient.newsPool
            self.filteredNewsPoolDB = self.MongoDBClient.filteredNewsPool
            self.infDB = self.MongoDBClient.influenceRanks
            self.PostGreSQLConnect = psycopg2.connect(
                "dbname='openmakerdb' user='openmakerpsql' host='138.68.92.181' password='smio1EUp'")
            self.cur = self.PostGreSQLConnect.cursor()

            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 15,
                host='138.68.92.181',
                port='5432',
                user='openmakerpsql',
                password='smio1EUp',
                database='openmakerdb')

            print("new connection")
        except Exception as e:
            print(e)
            print("I am unable to connect to the database")

    @contextmanager
    def get_cursor(self):
        conn = self.pg_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            self.pg_pool.putconn(conn)
