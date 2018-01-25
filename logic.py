import json
from threading import Thread
from crontab_module.crons import facebook_reddit_crontab

import facebook
import praw
import pymongo
import pprint
import tweepy

from application.utils import twitter_search_sample_tweets
from application.utils import delete_audience

from application.Connections import Connection

from decouple import config


def setCurrentTopic(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        topics = cur.fetchall()
        sql = (
            "SELECT topic_id "
            "FROM user_topic_subscribe "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        subscribed_topics = cur.fetchall()
        topics = topics + subscribed_topics
        sql = (
            "SELECT current_topic_id "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user = cur.fetchall()
        if user[0][0] is None and len(topics) != 0:
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [topics[0][0], int(user_id)])
        elif len(topics) == 0:
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [None, int(user_id)])

def getCurrentLocation(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT current_location "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user_location = cur.fetchone()
        if user_location[0] is None:
            sql = (
                "UPDATE users "
                "SET current_location = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, ['italy', int(user_id)])
            return 'italy'
        return user_location[0]


def saveTopicId(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE users "
            "SET current_topic_id = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(topic_id), int(user_id)])

def saveLocation(location, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE users "
            "SET current_location = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [location, int(user_id)])


def getCurrentTopic(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT current_topic_id "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        user = cur.fetchall()
        if user[0][0] is not None:
            sql = (
                "SELECT topic_id, topic_name "
                "FROM topics "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [int(user[0][0])])
            topic = cur.fetchall()
            return {'topic_id': topic[0][0], 'topic_name': topic[0][1]}
        else:
            return None


def addFacebookPagesAndSubreddits(topic_id, topic_list):
    print(topic_list)
    sources = sourceSelection(topic_list)
    with Connection.Instance().get_cursor() as cur:
        for facebook_page_id in sources['pages']:
            sql = (
                "INSERT INTO topic_facebook_page "
                "(topic_id, facebook_page_id) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(topic_id), facebook_page_id['page_id']])

        for subreddit in sources['subreddits']:
            sql = (
                "INSERT INTO topic_subreddit "
                "(topic_id, subreddit) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(topic_id), subreddit])

    pages = [facebook_page_id['page_id'] for facebook_page_id in sources['pages']]
    subreddits = [subreddit for subreddit in sources['subreddits']]
    facebook_reddit_crontab.triggerOneTopic(topic_id, topic_list, list(set(pages)), list(set(subreddits)))


def sourceSelection(topicList):
    return {'pages': sourceSelectionFromFacebook(topicList),
            'subreddits': sourceSelectionFromReddit(topicList)}


def sourceSelectionFromFacebook(topicList):
    my_token = config("FACEBOOK_TOKEN")
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")
    pages = []
    for topic in topicList:
        s = graph.get_object("search?q=" + topic + "&type=page&limit=3")
        for search in s["data"]:
            pages.append({"page_id": search["id"], "page_name": search["name"]})
        s = graph.get_object("search?q=" + topic + "&type=group&limit=3")
        for search in s["data"]:
            if search["privacy"] == "OPEN":
                pages.append({"page_id": search["id"], "page_name": search["name"]})
    return [i for n, i in enumerate(pages) if i not in pages[n + 1:]]


def sourceSelectionFromReddit(topicList):
    keys = {
        'client_id': config("REDDIT_CLIENT_ID"),
        'client_secret': config("REDDIT_CLIENT_SECRET"),
        'user_agent': config("REDDIT_USER_AGENT"),
        'api_type': config("REDDIT_API_TYPE")
    }
    reddit = praw.Reddit(client_id=keys["client_id"],
                         client_secret=keys["client_secret"],
                         user_agent=keys["user_agent"],
                         api_type=keys["api_type"])
    allSubreddits = []
    for topic in topicList:
        subreddits = reddit.subreddits.search_by_name(topic)
        if " " in topic:
            subreddits.extend(reddit.subreddits.search_by_name(topic.replace(" ", "_")))
            subreddits.extend(reddit.subreddits.search_by_name(topic.replace(" ", "")))
        subreddits = set([sub.display_name for sub in subreddits])
        allSubreddits = list(set(allSubreddits + list(subreddits)))
    return allSubreddits


def getAlertLimit(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT alertlimit "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        fetched = cur.fetchall()
        return fetched[0][0]

def register(username, password, country_code):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM users where username = %s)"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 1, 'message': 'Username already taken.'}

        sql = (
            "SELECT NOT EXISTS (SELECT 1 FROM country_code where country_code = %s)"
        )
        cur.execute(sql, [country_code])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 2, 'message': 'Invalid country code.'}

        sql = (
            "INSERT INTO users "
            "(username, password, alertlimit, country_code) "
            "VALUES (%s, %s, %s, %s)"
        )
        cur.execute(sql, [username,password, 5, country_code])

        sql = (
            "SELECT * "
            "FROM users "
            "WHERE username = %s"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchall()

        return {'response': True, 'user_id': fetched[0][0]}

def getUser(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT username, country_code "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        fetched = cur.fetchone()

        country = ""
        if fetched[1] is not None:
            country = fetched[1]

        return {'username': fetched[0], 'country': country}

def updateUser(user_id, password, country_code,auth_token, twitter_pin):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT NOT EXISTS (SELECT 1 FROM country_code where country_code = %s)"
        )
        cur.execute(sql, [country_code])
        fetched = cur.fetchone()

        if fetched[0]:
            return {'response': False, 'error_type': 1, 'message': 'Invalid country code.'}

        consumerKey = config("TWITTER_CONSUMER_KEY")
        consumerSecret = config("TWITTER_CONSUMER_SECRET")
        auth = tweepy.OAuthHandler(consumerKey,consumerSecret)
        auth.request_token = eval(auth_token)
        auth.secure=True
        token = auth.get_access_token(verifier=twitter_pin)

        if twitter_pin != '' and len(token) == 2:
            sql = (
                "UPDATE users "
                "SET password = %s, country_code = %s, twitter_access_token = %s, twitter_access_secret = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [password, country_code, token[0], token[1], user_id])
        else:
            sql = (
                "UPDATE users "
                "SET password = %s, country_code = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [password, country_code, user_id])

        return {'response': True}

def login(username, password):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM users "
            "WHERE username = %s"
        )
        cur.execute(sql, [username])
        fetched = cur.fetchall()
        if len(fetched) == 0:
            return {'response': False, 'error_type': 1, 'message': 'Invalid username'}

        if password != fetched[0][2]:
            return {'response': False, 'error_type': 2, 'message': 'Invalid password'}

        return {'response': True, 'user_id': fetched[0][0]}


def getAllRunningAlertList():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE is_running = %s"
        )
        cur.execute(sql, [True])
        var = cur.fetchall()
        alerts = [
            {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': sorted(i[3].split(",")), 'lang': sorted(i[4].split(","))}
            for i in var]
        return sorted(alerts, key=lambda k: k['alertid'])


# Gives alerts as lists
def getAlertList(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        own_topic_ids = [i[0] for i in var]

        sql = (
            "SELECT topic_id FROM user_topic_subscribe WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        subscribe_topic_ids = [i[0] for i in var]

        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id != %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        remaining_topics_topics = []
        for i in var:
            if i[0] not in subscribe_topic_ids:
                remaining_topics_topics.append(i[0])

        sql = (
            "SELECT * "
            "FROM topics;"
        )
        cur.execute(sql)
        var = cur.fetchall()

        alerts = []

        for i in var:
            sql = (
                "SELECT user_id FROM user_topic WHERE topic_id = %s ;"
            )
            cur.execute(sql, [i[0]])
            var = cur.fetchone()
            sql = (
                "SELECT username FROM users WHERE user_id = %s ;"
            )
            cur.execute(sql, [var[0]])
            var = cur.fetchone()
            temp_alert = {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': i[3].split(","), 'lang': i[4].split(","), \
             'creationTime': i[5], 'updatedTime': i[7], 'status': i[8], 'publish': i[9], 'created_by': var[0]}
            if i[0] in own_topic_ids:
                temp_alert['type'] = 'me'
            elif i[0] in subscribe_topic_ids:
                temp_alert['type'] = 'subscribed'
            elif i[0] in remaining_topics_topics:
                temp_alert['type'] = 'unsubscribed'
            alerts.append(temp_alert)

        alerts = sorted(alerts, key=lambda k: k['alertid'])
        for alert in alerts:
            alert['newsCount'] = Connection.Instance().newsPoolDB[str(alert['alertid'])].find().count()
            alert['audienceCount'] = Connection.Instance().audienceDB[str(alert['alertid'])].find().count()
            alert['eventCount'] = Connection.Instance().events[str(alert['alertid'])].find().count()
            alert['tweetCount'] = Connection.Instance().db[str(alert['alertid'])].find().count()
            try:
                hashtags = \
                    list(Connection.Instance().hashtags[str(alert['alertid'])].find({'name': 'month'},
                                                                                    {'month': 1, '_id': 0}))[0]['month']
            except:
                hashtags = []
                pass
            hashtags = ["#" + hashtag['hashtag'] for hashtag in hashtags]
            alert['hashtags'] = ", ".join(hashtags[:5])
        return alerts


def alertExist(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchone()
        if var is not None:
            return True
        else:
            return False


# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid is not None:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT * "
                "FROM topics "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [alertid])
            var = cur.fetchone()
            alert = {'alertid': var[0], 'name': var[1], 'description': var[2], 'keywords': var[3],
                     'lang': var[4].split(","), 'status': var[8],
                     'keywordlimit': var[6]}
    else:
        alert = {'alertid': "", 'name': "", 'keywords': "", 'lang': "", 'status': False, 'keywordlimit': 10,
                 'description': ""}
    return alert


# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alertid])
        var = cur.fetchone()
        print(var)
        alert = {'alertid': var[0], 'name': var[1], 'keywords': var[3].split(","), 'lang': var[4].split(","),
                 'status': var[8]}
        return alert


def setUserAlertLimit(user_id, setType):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT alertlimit "
            "FROM users "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        fetched = cur.fetchall()
        if setType == 'decrement':
            newLimit = fetched[0][0] - 1
        elif setType == 'increment':
            newLimit = fetched[0][0] + 1

        sql = (
            "UPDATE users "
            "SET alertlimit = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [newLimit, int(user_id)])


def banDomain(user_id, topic_id, domain):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_domain where user_id = %s and domain = %s)"
        )
        cur.execute(sql, [int(user_id), domain])
        fetched = cur.fetchone()

        if not fetched[0]:
            sql = (
                "INSERT INTO user_domain "
                "(user_id, domain) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [user_id, domain])
            Connection.Instance().filteredNewsPoolDB[str(topic_id)].update_many(
            {},
            {'$pull':{
                'yesterday': {'domain': domain},
                'week': {'domain': domain},
                'month': {'domain': domain}
            }})



# Take alert information, give an id and add it DB
def addAlert(alert, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO topics "
            "(topic_name, topic_description, keywords, languages, keyword_limit) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cur.execute(sql, [alert['name'], alert['description'], alert['keywords'], alert['lang'], alert['keywordlimit']])
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            "ORDER BY topic_id DESC "
            "LIMIT 1"
        )
        cur.execute(sql)
        topic = cur.fetchone()
        print(topic)

    if alert['name'] == topic[1]:
        sql = (
            "INSERT INTO user_topic "
            "(user_id, topic_id) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [int(user_id), int(topic[0])])
        alert = getAlertAllOfThemList(int(topic[0]))
        setUserAlertLimit(user_id, 'decrement')
        setCurrentTopic(user_id)
        t = Thread(target=addFacebookPagesAndSubreddits, args=(alert['alertid'], alert['keywords'],))
        t.start()


# Deletes alert and terminate its thread
def deleteAlert(alertid, user_id):
    alert = getAlertAllOfThemList(alertid)
    setUserAlertLimit(user_id, 'increment')
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alertid])
        topic = cur.fetchone()
        topic = list(topic)
        topic.append(int(user_id))
        sql = (
            "INSERT INTO public.archived_topics "
            "(topic_id, topic_name, topic_description, keywords, languages, creation_time, keyword_limit, last_tweet_date, is_running, is_publish, user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        )
        cur.execute(sql, topic)
        sql = (
            "DELETE FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alertid])
        sql = (
            "DELETE FROM user_topic "
            "WHERE topic_id = %s AND user_id = %s"
        )
        cur.execute(sql, [alertid, user_id])
        sql = (
            "DELETE FROM topic_facebook_page "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alertid])
        sql = (
            "DELETE FROM topic_subreddit "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alertid])
    setCurrentTopic(user_id)

    t = Thread(target=delete_audience.main, args=(alert['alertid'],))
    t.start()


# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET topic_description = %s, keywords = %s, languages = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [alert['description'], alert['keywords'], alert['lang'], alert['alertid']])
    alert = getAlertAllOfThemList(alert['alertid'])
    t = Thread(target=addFacebookPagesAndSubreddits, args=(alert['alertid'], alert['keywords'],))
    t.start()


# Starts alert streaming.
def startAlert(alertid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, alertid])
        alert = getAlertAllOfThemList(alertid)


# Stops alert streaming.
def stopAlert(alertid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, alertid])
        alert = getAlertAllOfThemList(alertid)


# Publishs the given alert
def publishAlert(alertid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, alertid])


# Unpublishs the given alert
def unpublishAlert(alertid):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, alertid])


def getBookmarks(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT bookmark_link_id "
            "FROM user_bookmark "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        bookmark_link_ids = [a[0] for a in cur.fetchall()]

        if len(bookmark_link_ids) == 0:
            bookmark_link_ids = [-1]

        sql = (
            "SELECT news_id, rating "
            "FROM user_news_rating "
            "WHERE user_id = %s and news_id IN %s"
        )
        cur.execute(sql, [int(user_id), tuple(bookmark_link_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

        news = []
        for alertid in Connection.Instance().newsPoolDB.collection_names():
            news = news + list(
                Connection.Instance().newsPoolDB[str(alertid)].find({'link_id': {'$in': bookmark_link_ids}}))

        for news_item in news:
            news_item['bookmark'] = True

            news_item['sentiment'] = 0
            try:
                news_item['sentiment'] = ratings[str(news_item['link_id'])]
            except KeyError:
                pass

        return news


# Adds bookmark
def addBookmark(topic_id, user_id, link_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO user_bookmark "
            "(user_id, bookmark_link_id) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [int(user_id), int(link_id)])


# Removes bookmarks
def removeBookmark(topic_id, user_id, link_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "DELETE FROM user_bookmark "
            "WHERE user_id = %s AND bookmark_link_id = %s"
        )
        cur.execute(sql, [int(user_id), int(link_id)])


def sentimentNews(topic_id, user_id, link_id, rating):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_news_rating where user_id = %s and topic_id = %s and news_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id), int(link_id)])
        fetched = cur.fetchone()

        if fetched[0]:
            sql = (
                "UPDATE user_news_rating "
                "SET rating = %s "
                "WHERE user_id = %s and news_id = %s and topic_id = %s"
            )
            cur.execute(sql, [float(rating), int(user_id), int(link_id), int(topic_id)])
        else:
            sql = (
                "INSERT INTO user_news_rating "
                "(user_id, news_id, topic_id, rating) "
                "VALUES (%s, %s, %s, %s)"
            )
            cur.execute(sql, [int(user_id), int(link_id), int(topic_id), float(rating)])


def rateAudience(topic_id, user_id, audience_id, rating):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_audience_rating where user_id = %s and topic_id = %s and audience_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id), int(audience_id)])
        fetched = cur.fetchone()

        if fetched[0]:
            if float(rating) != 0.0:
                sql = (
                    "UPDATE user_audience_rating "
                    "SET rating = %s "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [float(rating), int(user_id), int(audience_id), int(topic_id)])
            else:
                sql = (
                    "DELETE FROM user_audience_rating "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id)])
        else:
            if float(rating) != 0.0:
                sql = (
                    "INSERT INTO user_audience_rating "
                    "(user_id, audience_id, topic_id, rating) "
                    "VALUES (%s, %s, %s, %s)"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id), float(rating)])

def hideInfluencer(topic_id, user_id, influencer_id, description, is_hide, location):
    #print("in hide influencer:")
    #print(influencer_id)
    print("In hide influencer")
    print("Topic id:" + str(topic_id))
    print("Location:" + location)
    influencer_id = int(influencer_id)
    print(influencer_id)
    if is_hide == True:
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

def getTweets(alertid):
    tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                              'created_at': 1, "_id": 0}).sort(
        [('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


# Runs we scroll the page
def getSkipTweets(alertid, lastTweetId):
    tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$lt': int(lastTweetId)}},
                                                         {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                          'created_at': 1, "_id": 0}).sort(
        [('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    return tweets


# Checks periodically new tweets
def checkTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                  'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}},
                                                             {'tweetDBId': 1, "text": 1, "user": 1, 'created_at': 1,
                                                              "_id": 0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)


# Gets newest tweets and returns them
def getNewTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text": 1, "id": 1, "user": 1,
                                                                  'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}},
                                                             {'tweetDBId': 1, 'id': 1, "text": 1, "user": 1,
                                                              'created_at': 1, "_id": 0}).sort(
            [('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return tweets


# Return preview alert search tweets
def searchNews(keywords, languages):
    keys = keywords.split(",")
    result_keys = []
    for key in keys:
        if " " in key:
            result_keys.append("\"" + key + "\"")
        else:
            result_keys.append(key)
    # ends
    keywords = " OR ".join(result_keys)
    languages = " OR ".join(languages.split(","))
    news = twitter_search_sample_tweets.getNewsFromTweets(keywords, languages)
    return news


def getNews(user_id, alertid, date, cursor):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        topics = cur.fetchall()



    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    feeds = list(Connection.Instance().filteredNewsPoolDB[str(alertid)].find({'name': date}, {date: 1}))
    link_ids = []
    if len(feeds) != 0:
        feeds = list(feeds[0][date][cursor:cursor + 20])
        link_ids = [news['link_id'] for news in feeds]

    if len(link_ids) == 0:
        link_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT news_id, rating "
            "FROM user_news_rating "
            "WHERE user_id = %s and topic_id = %s and news_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(alertid), tuple(link_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

        sql = (
            "SELECT bookmark_link_id "
            "FROM user_bookmark "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        bookmarks = [link_id[0] for link_id in cur.fetchall()]

    for feed in feeds:
        feed['bookmark'] = False
        if feed['link_id'] in bookmarks:
            feed['bookmark'] = True

        feed['sentiment'] = 0
        try:
            feed['sentiment'] = ratings[str(feed['link_id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 20
    if cursor >= 60 or len(feeds) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 60
    result['feeds'] = feeds
    return result

def getAudiences(topic_id, user_id, cursor, location):
    result = {}
    audiences = list(Connection.Instance().audience_samples_DB[str(location)+"_"+str(topic_id)].find({}))[cursor:cursor + 21]
    audience_ids = []
    if len(audiences) != 0:
        audience_ids = [audience['id'] for audience in audiences]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for audience in audiences:

        audience['rate'] = 0
        try:
            audience['rate'] = ratings[str(audience['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audiences) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audiences'] = audiences
    return result

def getLocalInfluencers(topic_id, cursor, location):
    print("In get local infs")
    print("Topic id:" + str(topic_id))
    print("Location:" + location)
    result = {}
    local_influencers = list(Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)].find({}))[cursor:cursor + 21]

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
        #print("Hidden ids:")
        #print(hidden_ids)
        for influencer in local_influencers:
            if str(influencer['id']) in hidden_ids:
                #print(str(influencer['id']) + " is hidden")
                influencer['hidden']=True
            else:
                influencer['hidden']=False
                #print(str(influencer['id']) + " not hidden")

    cursor = int(cursor) + 21
    if cursor >= 500 or len(local_influencers) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['local_influencers'] = local_influencers
    return result

def getRecommendedAudience(topic_id, location, filter, user_id, cursor):
    result = {}
    if filter == "rated":
        # fetch rated audience
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT audience_id "
                "FROM user_audience_rating "
                "WHERE user_id = %s and topic_id = %s ;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            rated_audience = cur.fetchall()
            rated_audience = [aud_member[0] for aud_member in rated_audience]
            audience = Connection.Instance().audienceDB['all_audience'].find({'id':{'$in':rated_audience}})

    elif filter == "recommended":
        # fetch recommended audience
        audience = Connection.Instance().audience_samples_DB[str(location)+ '_'+str(topic_id)].find({})

    else:
        print("Please provide a valid filter. \"rated\" or \"recommended\"")
        return
    audience = list(audience)[cursor:cursor + 21]

    audience_ids = []
    if len(audience) != 0:
        audience_ids = [aud_member['id'] for aud_member in audience]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for aud_member in audience:
        aud_member['rate'] = 0
        try:
            aud_member['rate'] = ratings[str(aud_member['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audience) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audience'] = audience
    return result


def subsribeTopic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()

        if not fetched[0]:
            sql = (
                "INSERT INTO user_topic_subscribe "
                "(user_id, topic_id) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])


def unsubsribeTopic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()
        if fetched[0]:
            sql = (
                "DELETE FROM user_topic_subscribe "
                "WHERE user_id = %s and topic_id = %s;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [None, int(user_id)])

def getRelevantLocations():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM relevant_locations;"
        )
        cur.execute(sql, [])
        locations = cur.fetchall()
        return [{'location_name': i[0], 'location_code': i[1]} for i in locations]

def getTwitterAuthUrl():
    consumerKey = config("TWITTER_CONSUMER_KEY")
    consumerSecret = config("TWITTER_CONSUMER_SECRET")

    #authenticating twitter consumer key
    auth = tweepy.OAuthHandler(consumerKey,consumerSecret)
    auth.secure=True
    return (auth.get_authorization_url(), auth.request_token)
