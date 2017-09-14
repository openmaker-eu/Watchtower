import json
import re
from datetime import datetime
from time import gmtime, strftime, strptime
from threading import Thread
import facebook_reddit_crontab

import facebook
import praw
import pymongo

import date_filter
import twitter_search_sample_tweets
from application.Connections import Connection


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


def saveTopicId(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE users "
            "SET current_topic_id = %s "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(topic_id), int(user_id)])


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
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
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
    keys = Connection.Instance().redditFacebookDB['tokens'].find_one()["reddit"]
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
            {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': i[3].split(","), 'lang': i[4].split(",")}
            for i in var]
        return alerts


# Gives alerts as lists
def getAlertList(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * FROM ( "
            "SELECT * FROM ( "
            "SELECT topic_id FROM user_topic WHERE user_id = %s "
            ") AS ut "
            "INNER JOIN topics AS t "
            "ON t.topic_id = ut.topic_id) as a"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()
        alerts = [
            {'alertid': i[1], 'name': i[2], 'description': i[3], 'keywords': i[4].split(","), 'lang': i[5].split(","), \
             'creationTime': i[6], 'updatedTime': i[8], 'status': i[9], 'publish': i[10]} for i in var]
        alerts = sorted(alerts, key=lambda k: k['alertid'])
        for alert in alerts:
            alert['tweetCount'] = Connection.Instance().db[str(alert['alertid'])].find().count()
            hashtags = \
                list(Connection.Instance().hashtags[str(alert['alertid'])].find({'name': 'month'},
                                                                                {'month': 1, '_id': 0}))[0]['month']
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


def banDomain(user_id, domain):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO user_domain "
            "(user_id, domain) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [user_id, domain])


# Take alert information, give an id and add it DB
def addAlert(alert, mainT, user_id):
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
        mainT.addAlert(alert)
        setCurrentTopic(user_id)
        t = Thread(target=addFacebookPagesAndSubreddits, args=(alert['alertid'], alert['keywords'],))
        t.start()


# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT, user_id):
    alert = getAlertAllOfThemList(alertid)
    setUserAlertLimit(user_id, 'increment')
    mainT.delAlert(alert)
    Connection.Instance().db[str(alertid)].drop()
    Connection.Instance().newsPoolDB[str(alertid)].drop()
    Connection.Instance().newsdB[str(alertid)].drop()
    with Connection.Instance().get_cursor() as cur:
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


# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT, user_id):
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
    mainT.updateAlert(alert)


# Starts alert streaming.
def startAlert(alertid, mainT):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, alertid])
        alert = getAlertAllOfThemList(alertid)
        mainT.addAlert(alert)


# Stops alert streaming.
def stopAlert(alertid, mainT):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, alertid])
        alert = getAlertAllOfThemList(alertid)
        mainT.delAlert(alert)


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

        news = []
        for alertid in Connection.Instance().newsPoolDB.collection_names():
            news = news + list(
                Connection.Instance().newsPoolDB[str(alertid)].find({'link_id': {'$in': bookmark_link_ids}}))

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
        updateNewsFeed(topic_id, user_id)
        content = """<a href="javascript:;" onclick="dummy('remove', '{}')"><span style="float:center;color:#808080;" class="glyphicon glyphicon-bookmark"></span></a>""".format(
            link_id)
        return content


# Removes bookmarks
def removeBookmark(topic_id, user_id, link_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "DELETE FROM user_bookmark "
            "WHERE user_id = %s AND bookmark_link_id = %s"
        )
        cur.execute(sql, [int(user_id), int(link_id)])
        updateNewsFeed(topic_id, user_id)
        content = """<a href="javascript:;" onclick="dummy('add', '{}')" style="color: #000000;text-decoration: none;"><span style="float:right;color:#D70000;font-size:24px" align="right" class="glyphicon glyphicon-bookmark"></span></a>""".format(
            link_id)
        return content


def updateNewsFeed(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT domain "
            "FROM user_domain "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [int(user_id)])
        domains = [a[0] for a in cur.fetchall()]
        date_filter.calc(topic_id, domains)


def sentimentPositive(alertid, user_id, link_id):
    link_id = int(link_id)
    Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'link_id': link_id}, {'$set': {'sentiment': 1}})
    updateNewsFeed(alertid, user_id)
    content = """<a href="javascript:;" onclick="sentiment('negative', '{}')">
<span style="display:inline;color:#BDBDBD" class="glyphicon glyphicon-remove-sign"></span>
</a>
<a href="javascript:;" onclick="sentiment('positive', '{}')">
<span style="display:inline;color:#66BB6A" class="glyphicon glyphicon-ok-sign"></span>
</a>""".format(link_id, link_id, link_id)
    return content


def sentimentNegative(alertid, user_id, link_id):
    link_id = int(link_id)
    Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'link_id': link_id},
                                                                       {'$set': {'sentiment': -1}})
    updateNewsFeed(alertid, user_id)
    content = """<a href="javascript:;" onclick="sentiment('negative', '{}')">
<span style="display:inline;color:#66BB6A" class="glyphicon glyphicon-remove-sign"></span>
</a>
<a href="javascript:;" onclick="sentiment('positive', '{}')">
<span style="display:inline;color:#BDBDBD" class="glyphicon glyphicon-ok-sign"></span>
</a>""".format(link_id, link_id, link_id)
    return content


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


def getNews(alertid, date, cursor):
    dates = ['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    feeds = list(Connection.Instance().filteredNewsPoolDB[str(alertid)].find({'name': date}, {date: 1}))
    feeds = list(feeds[0][date][cursor:cursor + 20])

    cursor = int(cursor) + 20
    if cursor >= 60:
        cursor = 60
    result['next_cursor'] = cursor
    result['cursor_length'] = 60
    result['feeds'] = feeds
    return result


def getAudiences(alertid):
    return list(Connection.Instance().infDB[str(alertid)].find({}).sort([('rank', pymongo.ASCENDING)]))
