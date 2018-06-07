# Author: Kemal Berk Kocabagli

import sys
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))

from .get_follower_ids import *

# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def main():
    with Connection.Instance().get_cursor() as cur:
        # Get jobs that have not been processed
        sql = (
            "SELECT influencer_id "
            "FROM fetch_followers_job_queue "
            "WHERE status = 'created'"
        )
        try:
            cur.execute(sql)
        except:
            print("Could not fetch influencer ids whose followers will be retrieved.")

        influencer_ids = [int(e[0]) for e in cur.fetchall()]

    for influencer in Connection.Instance().influencerDB['all_influencers'].find({'id': {'$in': influencer_ids}}):
        print("Fetching followers of  " + influencer['screen_name'] + " (id: " + str(influencer['id']) + ")...")

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "UPDATE fetch_followers_job_queue "
                "SET status = 'processing' "
                "WHERE influencer_id = %(id)s "
            )
            try:
                cur.execute(sql, {'id': str(influencer['id'])})
                print("aBC")
            except:
                print("Error updating influencer status to processing.")

        print("Updated status to processing.")

        try:
            get_follower_ids_by_influencer(influencer)
        except:
            with Connection.Instance().get_cursor() as cur:
                sql = (
                    "UPDATE fetch_followers_job_queue "
                    "SET status = 'failed' "
                    "WHERE influencer_id = %(id)s "
                )
                try:
                    cur.execute(sql, {'id': str(influencer['id'])})
                except:
                    print("Error updating influencer status to failed.")

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "UPDATE fetch_followers_job_queue "
                "SET status = 'finished' , updated_time = %(updated_time)s"
                "WHERE influencer_id = %(id)s "
            )
            try:
                cur.execute(sql, {'id': str(influencer['id']), 'updated_time': datetime.utcnow()})
            except:
                print("Error updating influencer status to finished.")


if __name__ == "__main__":
    main()
