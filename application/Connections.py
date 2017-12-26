from __future__ import print_function

import psycopg2
import pymongo
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
import urllib.request
import re
import sys
from decouple import config

from application.utils.Singleton import Singleton

@Singleton
class Connection:
    def __init__(self):
        try:
            hosts = ['138.68.92.181', '194.116.76.78']

            with urllib.request.urlopen('http://ipinfo.io/ip') as response:
                html = response.read()

            a = re.findall("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", str(html))

            h = a[0]

            if h in hosts:
                host = h
            else:
                if len(sys.argv) > 1:
                    host = sys.argv[1]
                else:
                    print("Please select a host: ")
                    for i in range(0, len(hosts)):
                        print(str(i+1) + "->" + hosts[i])

                    host = hosts[int(input())-1]

            self.machine_host = host

            self.MongoDBClient = pymongo.MongoClient('mongodb://'+config("MONGODB_USER")+":"+config("MONGODB_PASSWORD")+'@'+host+':27017/', connect=False)
            self.db = self.MongoDBClient.openMakerdB
            self.newsdB = self.MongoDBClient.newsdB
            self.feedDB = self.MongoDBClient.feedDB
            self.conversations = self.MongoDBClient.conversations
            self.events = self.MongoDBClient.events
            self.hashtags = self.MongoDBClient.hashtags
            self.newsPoolDB = self.MongoDBClient.newsPool
            self.filteredNewsPoolDB = self.MongoDBClient.filteredNewsPool

            # AUDIENCE
            self.influencerDB = self.MongoDBClient.influencers_test # db for influencers
            self.audienceDB = self.MongoDBClient.audience_test # db for audience
            self.audience_samples_DB = self.MongoDBClient.audience_samples # db for audience samples
            self.local_influencers_DB = self.MongoDBClient.local_influencers # db for local influencers
            self.audience_networks_DB = self.MongoDBClient.audience_networks # db for audience networks

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

    @contextmanager
    def get_cursor(self):
        conn = self.pg_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            self.pg_pool.putconn(conn)
