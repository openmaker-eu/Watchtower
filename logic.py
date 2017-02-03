import re
import search
import pymongo
from application.Connections import Connection


# Setups server
def setupServer():
    alerts = getAlertList()
    for alert in alerts:
        Connection.Instance().cur.execute("update alerts set isAlive=%s where id = %s;", [True, alert['id']])
        Connection.Instance().PostGreSQLConnect.commit()

# Gives alerts as lists
def getAlertList():
    Connection.Instance().cur.execute("Select * from alerts;")
    var = Connection.Instance().cur.fetchall()
    alerts = [ {'id':str(i[0]), 'name':i[1], 'keywords':i[2].split(","), 'lang': i[3].split(","), 'status': i[4]} for i in var   ]
    return alerts

# Login check
def login(userDic):
    Connection.Instance().cur.execute("Select * from users;")
    var = Connection.Instance().cur.fetchall()
    return var[0][0] == userDic['username'] and var[0][1] == userDic['password']

# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid != None:
        Connection.Instance().cur.execute("Select * from alerts where id = %s;", [alertid])
        var = Connection.Instance().cur.fetchone()
        alert = {'id': str(var[0]), 'name':var[1], 'keywords':var[2], 'lang': var[3].split(","), 'status': var[4]}
    else:
        alert = {'id': "", 'name': "", 'keywords': "", 'lang': "", 'status': False}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    Connection.Instance().cur.execute("Select * from alerts where id = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    alert = {'id':var[0], 'name':var[1], 'keywords':var[2].split(","), 'lang': var[3].split(","), 'status': var[4]}
    return alert

# Give nextalertid
def getNextAlertId():
    Connection.Instance().cur.execute("select id from alerts order by id desc limit 1;")
    rows = Connection.Instance().cur.fetchall()
    if(len(rows) == 0):
        return 0
    else:
        for temp in rows:
            return temp[0]+1

# Take alert information, give an id and add it DB
def addAlert(alert, mainT):
    alert['id'] = getNextAlertId()
    Connection.Instance().cur.execute("INSERT INTO alerts (id, alertname, keywords,lang, isAlive) values (%s, %s, %s, %s, %s);", [alert['id'] , alert['name'], alert['keywords'], alert['lang'], True])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['id'])
    mainT.addThread(alert)

# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT):
    Connection.Instance().cur.execute("update alerts set keywords = %s ,lang = %s, isAlive=%s where id = %s;", [alert['keywords'], alert['lang'],True, alert['id']])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['id'])
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)
    Connection.Instance().db[str(alert['id'])].drop()
    mainT.addThread(alert)

# Starts alert streaming.
def startAlert(alertid, mainT):
    Connection.Instance().cur.execute("update alerts set isAlive = %s where id = %s;", [True, alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alertid)
    mainT.addThread(alert)

# Stops alert streaming.
def stopAlert(alertid, mainT):
    Connection.Instance().cur.execute("update alerts set isAlive = %s where id = %s;", [False, alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alertid)
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)

# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT):
    alert = getAlertAllOfThemList(alertid)
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)
    Connection.Instance().db[str(alertid)].drop()
    Connection.Instance().cur.execute("delete from alerts where id = %s;", [alertid])
    Connection.Instance().PostGreSQLConnect.commit()

def getTweets(alertid):
    tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
    return tweets

# Runs we scroll the page
def getSkipTweets(alertid, lastTweetId):
    tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$lt': int(lastTweetId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
    return tweets

# Checks periodically new tweets
def checkTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)

# Gets newest tweets and returns them
def getNewTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
    return tweets

# Return preview alert search tweets
def searchTweets(keywords, languages):
    keys = keywords.split(",")
    keywords = " OR ".join(keywords.split(","))
    languages = " OR ".join(languages.split(","))
    tweets = search.getTweets(keywords, languages)
    for tweet in tweets:
        for keyword in keys:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
    return tweets
