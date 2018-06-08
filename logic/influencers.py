__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

import tweepy
from decouple import config

from application.Connections import Connection

# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def add_local_influencer(topic_id, location, screen_name):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO added_influencers "
            "(topic_id, country_code, screen_name) "
            "VALUES (%s, %s, %s)"
        )
        cur.execute(sql, [int(topic_id), str(location), str(screen_name), ""])

    if Connection.Instance().added_local_influencers_DB['added_influencers'].find_one(
            {"screen_name": screen_name}) is None:
        new_local_influencer = api.get_user(screen_name)
        new_local_influencer['topics'] = topic_id
        new_local_influencer['locations'] = location
        Connection.Instance().added_local_influencers_DB['added_influencers'].insert_one(new_local_influencer)
    else:
        Connection.Instance().added_local_influencers_DB['added_influencers'].update(
            {"screen_name": screen_name},
            {
                "$addToSet": {
                    "topics": topic_id,
                    "locations": location
                }
            }
        )


def hide_influencer(topic_id, user_id, influencer_id, description, is_hide, location):
    # print("in hide influencer:")
    # print(influencer_id)
    print("In hide influencer")
    print("Topic id:" + str(topic_id))
    print("Location:" + location)
    influencer_id = int(influencer_id)
    print(influencer_id)
    if is_hide:
        print("Hiding influencer with ID:" + str(influencer_id))
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "INSERT INTO hidden_influencers "
                "(topic_id, country_code, influencer_id, description) "
                "VALUES (%s, %s, %s, %s)"
            )
            cur.execute(sql, [int(topic_id), str(location), str(influencer_id), ""])
    else:
        print("Unhiding influencer with ID:" + str(influencer_id))
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "DELETE FROM hidden_influencers "
                "WHERE topic_id = %s and country_code = %s and influencer_id = %s "
            )
            cur.execute(sql, [int(topic_id), str(location), str(influencer_id)])


def get_local_influencers(topic_id, cursor, location):
    print("In get local infs")
    print("Topic id: " + str(topic_id))
    print("Location: " + location)
    result = {}
    local_influencers = []

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT influencer_id "
            "FROM hidden_influencers "
            "WHERE country_code = %s and topic_id = %s "
        )
        cur.execute(sql, [str(location), int(topic_id)])
        hidden_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]
        # print("Hidden ids:")
        # print(hidden_ids)

    if location.lower() == "global":
        local_influencers += list(Connection.Instance().influencerDB["all_influencers"].find({"topics": topic_id}))[
                             cursor:cursor + 21]
    else:
        local_influencers += list(
            Connection.Instance().local_influencers_DB[str(topic_id) + "_" + str(location)].find({}))[
                             cursor:cursor + 21]

    for inf in local_influencers:
        inf['id'] = str(inf['id'])

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT influencer_id "
            "FROM hidden_influencers "
            "WHERE country_code = %s and topic_id = %s "
        )
        cur.execute(sql, [str(location), int(topic_id)])
        hidden_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]

        sql = (
            "SELECT influencer_id "
            "FROM fetch_followers_job_queue "
        )
        cur.execute(sql)
        fetching_ids = [str(influencer_id[0]) for influencer_id in cur.fetchall()]

        for influencer in local_influencers:
            if str(influencer['id']) in hidden_ids:
                influencer['hidden'] = True
            else:
                influencer['hidden'] = False
            if str(influencer['id']) in fetching_ids:
                influencer['in_fetch_followers_queue'] = True
            else:
                influencer['in_fetch_followers_queue'] = False

    # Convert last refreshed and last processed to date from datetime for readability
    for influencer in local_influencers:
        if 'last_refreshed' in influencer:
            dt = influencer['last_refreshed']
            influencer['last_refreshed'] = dt.date()
        if 'last_processed' in influencer:
            dt = influencer['last_processed']
            influencer['last_processed'] = dt.date()

    cursor = int(cursor) + 21
    if cursor >= 500 or len(local_influencers) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['local_influencers'] = local_influencers
    return result
