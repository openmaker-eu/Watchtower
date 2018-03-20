# -*- coding: utf-8 -*-
import sys
import pdb
from decouple import config # to get current working directory
sys.path.insert(0, config("ROOT_DIR"))

from application.Connections import Connection


if __name__ == "__main__":
    # Sort the audience samples and write top 20 to local_influencers database
    for collection_name in Connection.Instance().audience_samples_DB.collection_names():
        collection = Connection.Instance().audience_samples_DB[collection_name]
        pdb.set_trace()
        influencers = list(collection.find({}).sort([("influencer_score" , -1)]).limit(20))
        location, topic = collection_name.split("_")
        local_influencers_collection = Connection.Instance().local_influencers_DB[topic+"_"+location]
        local_influencers_collection.drop()
        local_influencers_collection.insert_many(influencers)
