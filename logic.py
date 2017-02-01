import pymongo
import psycopg2
import re
import search

# MongoDB
client = pymongo.MongoClient('138.68.92.181', 27017)
db = client.openMakerdB
# PostgreSQL
try:
    conn = psycopg2.connect("dbname='postgres' user='postgres' host='138.68.92.181' port='5432' password='a'")
except Exception as e:
    print e
    print "I am unable to connect to the database"
cur = conn.cursor()

# Setups server
def setupServer():
    alerts = getAlertList()
    for alert in alerts:
        cur.execute("update alerts set isAlive=%s where id = %s;", [True, alert['id']])
        conn.commit()

# Gives alerts as lists
def getAlertList():
    cur.execute("Select * from alerts;")
    var = cur.fetchall()
    alerts = [ {'id':str(i[0]), 'name':i[1], 'keywords':i[2].split(","), 'lang': i[3].split(","), 'status': i[4]} for i in var   ]
    return alerts

# Login check
def login(userDic):
    cur.execute("Select * from users;")
    var = cur.fetchall()
    return var[0][0] == userDic['username'] and var[0][1] == userDic['password']

# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid != None:
        cur.execute("Select * from alerts where id = %s;", [alertid])
        var = cur.fetchone()
        alert = {'id': str(var[0]), 'name':var[1], 'keywords':var[2], 'lang': var[3].split(","), 'status': var[4]}
    else:
        alert = {'id': "", 'name': "", 'keywords': "", 'lang': "", 'status': False}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    cur.execute("Select * from alerts where id = %s;", [alertid])
    var = cur.fetchone()
    alert = {'id':var[0], 'name':var[1], 'keywords':var[2].split(","), 'lang': var[3].split(","), 'status': var[4]}
    return alert

# Give nextalertid
def getNextAlertId():
    cur.execute("select id from alerts order by id desc limit 1;")
    rows = cur.fetchall()
    if(len(rows) == 0):
        return 0
    else:
        for temp in rows:
            return temp[0]+1

# Take alert information, give an id and add it DB
def addAlert(alert, mainT):
    alert['id'] = getNextAlertId()
    cur.execute("INSERT INTO alerts (id, alertname, keywords,lang, isAlive) values (%s, %s, %s, %s, %s);", [alert['id'] , alert['name'], alert['keywords'], alert['lang'], True])
    conn.commit()
    alert = getAlertAllOfThemList(alert['id'])
    mainT.addThread(alert)

# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT):
    cur.execute("update alerts set keywords = %s ,lang = %s, isAlive=%s where id = %s;", [alert['keywords'], alert['lang'],True, alert['id']])
    conn.commit()
    alert = getAlertAllOfThemList(alert['id'])
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)
    db[str(alert['id'])].drop()
    mainT.addThread(alert)

# Starts alert streaming.
def startAlert(alertid, mainT):
    cur.execute("update alerts set isAlive = %s where id = %s;", [True, alertid])
    conn.commit()
    alert = getAlertAllOfThemList(alertid)
    mainT.addThread(alert)

# Stops alert streaming.
def stopAlert(alertid, mainT):
    cur.execute("update alerts set isAlive = %s where id = %s;", [False, alertid])
    conn.commit()
    alert = getAlertAllOfThemList(alertid)
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)

# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT):
    alert = getAlertAllOfThemList(alertid)
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)
    db[str(alertid)].drop()
    cur.execute("delete from alerts where id = %s;", [alertid])
    conn.commit()

def getTweets(alertid):
    tweets = db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
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
    tweets = db[str(alertid)].find({'tweetDBId': {'$lt': int(lastTweetId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
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
    if newestId == -1:
        tweets = db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)

# Gets newest tweets and returns them
def getNewTweets(alertid, newestId):
    if newestId == -1:
        tweets = db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
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
