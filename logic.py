import pymongo
import psycopg2
import re

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

# Gives alerts as lists
def getAlertList():
    cur.execute("Select * from alerts;")
    var = cur.fetchall()
    alerts = [ {'id':str(i[0]), 'name':i[1], 'keywords':i[2].split(","), 'lang': i[3].split(",")} for i in var   ]
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
        alert = {'id': str(var[0]), 'name':var[1], 'keywords':var[2], 'lang': var[3].split(",")}
    else:
        alert = {'id': "", 'name': "", 'keywords': "", 'lang': ""}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    cur.execute("Select * from alerts where id = %s;", [alertid])
    var = cur.fetchone()
    alert = {'id':var[0], 'name':var[1], 'keywords':var[2].split(","), 'lang': var[3].split(",")}
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
    cur.execute("INSERT INTO alerts (id, alertname, keywords,lang) values (%s, %s, %s, %s);", [alert['id'] , alert['name'], alert['keywords'], alert['lang']])
    conn.commit()
    alert = getAlertAllOfThemList(alert['id'])
    mainT.addThread(alert)

# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT):
    cur.execute("update alerts set keywords = %s ,lang = %s where id = %s;", [alert['keywords'], alert['lang'], alert['id']])
    conn.commit()
    alert = getAlertAllOfThemList(alert['id'])
    if str(alert['id']) in mainT.getThreadDic():
        mainT.killThread(alert)
    db[str(alert['id'])].drop()
    mainT.addThread(alert)

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
    print alertid
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
    return tweets
