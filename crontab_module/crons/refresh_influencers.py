import numpy as np
from decouple import config
import datetime

import tweepy  # Twitter API helper package
import pymongo
from tweepy import OAuthHandler

import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))

from application.Connections import Connection

consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

GET_PROFILE_RATE_LIMIT = 100


def refresh_influencers(influencer_ids):
    """
    Fetches the Twitter profiles of 100 influencers (for refresh)
    Updates the 'all_influencers' collection with recent information
    """
    influencers = []
    try:
        influencers = [inf._json for inf in api.lookup_users(influencer_ids)]  # (!) max size limit of user_ids = 100
    except tweepy.TweepError as twperr:
        # it means the user account has been suspended, protected or closed.
        print(twperr)
        pass

    operations = []
    for influencer in influencers:
        influencer['last_refreshed'] = datetime.datetime.now()

        operations.append(
            pymongo.UpdateOne(
                {'id': influencer['id']},
                {'$set': influencer}
            )
        )

    # max size of operations will be 100 (rate limit).
    if len(operations) != 0:
        try:
            Connection.Instance().influencerDB['all_influencers'].bulk_write(operations, ordered=False)
        except Exception as e:
            print(e)
    print("Successfully refreshed the profiles of " + str(len(influencer_ids)) + " influencers.")


# REFRESH INFLUENCERS PERIODICALLY
def refresh_all_influencers():
    influencer_ids = Connection.Instance().influencerDB['all_influencers'].distinct('id')
    n = len(influencer_ids)
    # Process influencers batch by batch
    batch_size = GET_PROFILE_RATE_LIMIT
    no_batches = int(np.ceil(n / batch_size))
    print("Number of batches to process: " + str(no_batches))

    for i in range(no_batches):
        print("Processing batch " + str(i))
        current_batch_size = min(batch_size, n - i * batch_size)
        batch = influencer_ids[:current_batch_size]
        refresh_influencers(batch)
        del influencer_ids[:current_batch_size]  # delete the already processed influencers


def main():
    refresh_all_influencers()


if __name__ == "__main__":
    main()
