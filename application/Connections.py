from __future__ import print_function

from contextlib import contextmanager

import psycopg2
import pymongo
from decouple import config
from psycopg2.pool import ThreadedConnectionPool

from application.utils.Singleton import Singleton


@Singleton
class Connection:
    def __init__(self):
        try:
            host = config("HOST_IP")

            self.MongoDBClient = pymongo.MongoClient(
                'mongodb://' + config("MONGODB_USER") + ":" + config("MONGODB_PASSWORD") + '@' + host + ':27017/',
                connect=False)
            self.db = self.MongoDBClient.openMakerdB
            self.newsdB = self.MongoDBClient.newsdB
            self.feedDB = self.MongoDBClient.feedDB
            self.conversations = self.MongoDBClient.conversations
            self.events = self.MongoDBClient.events
            self.hashtags = self.MongoDBClient.hashtags
            self.newsPoolDB = self.MongoDBClient.newsPool
            self.filteredNewsPoolDB = self.MongoDBClient.filteredNewsPool
            self.infDB = self.MongoDBClient.influenceRanks
            self.tweetsDB = self.MongoDBClient.tweetsDB
            self.daily_hastags = self.MongoDBClient.daily_hastags
            self.daily_mentions = self.MongoDBClient.daily_mentions

            self.challengesDB = self.MongoDBClient.challenges

            # AUDIENCE
            self.influencerDB = self.MongoDBClient.influencers_test  # db for influencers
            self.audienceDB = self.MongoDBClient.audience_test  # db for audience
            self.audience_samples_DB = self.MongoDBClient.audience_samples  # db for audience samples
            self.local_influencers_DB = self.MongoDBClient.local_influencers  # db for local influencers
            self.audience_networks_DB = self.MongoDBClient.audience_networks  # db for audience networks

            # POSTGRE - INFO ABOUT TOPICS IS HELD HERE.
            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 15,
                host=host,
                port='5432',
                user=config("POSTGRESQL_USER"),
                password=config("POSTGRESQL_PASSWORD"),
                database=config("POSTGRESQL_DB"))

            print("new connection")
        except Exception as e:
            print(e)
            print("I am unable to connect to the database")

    def __getattribute__(self, name):
        if name == 'pg_pool':
            return object.__getattribute__(self, name)
        try:
            object.__getattribute__(self, 'MongoDBClient').server_info()
            return object.__getattribute__(self, name)
        except:
            count = 0
            while count < 3:
                print('I am trying to MongoDB server iteration #' + str(count))
                object.__setattr__(self, 'MongoDBClient', pymongo.MongoClient(
                    'mongodb://' + config("MONGODB_USER") + ":" + config("MONGODB_PASSWORD") + '@' + config(
                        "HOST_IP") + ':27017/',
                    connect=False))
                try:
                    object.__getattribute__(self, 'MongoDBClient').server_info()
                    break
                except:
                    pass
                count += 1
                if count == 3:
                    raise Exception("I am unable to connect to the mongodb")

            return object.__getattribute__(self, name)

    @contextmanager
    def get_cursor(self):
        conn = self.pg_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            self.pg_pool.putconn(conn)
