import re
import search
import pymongo
from application.Connections import Connection
from time import gmtime, strftime
import json

def getThemes():
    names = Connection.Instance().feedDB.collection_names()
    themes = [{'name': name} for name in names]
    return json.dumps(themes)

def getInfluencers(themename):
    influencers = Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0})
    influencers = list(influencers)
    return json.dumps(influencers)

def getFeeds(themename):
    feeds = Connection.Instance().feedDB[str(themename)].find({}, {"_id":0})
    feeds = list(feeds)
    return json.dumps(feeds)

def getAlertLimit(userid):
    Connection.Instance().cur.execute("select alertlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    return fetched[0][0]

def getUserInfo(username):
    Connection.Instance().cur.execute("select * from users where username = %s", [username])
    fetched = Connection.Instance().cur.fetchall()
    return {'userid': fetched[0][0], 'password': fetched[0][2]}

# Response of Alerts
def response(alertid):
    Connection.Instance().cur.execute("select threadstatus from alerts where alertid = %s", [alertid])
    fetched = Connection.Instance().cur.fetchall()
    if len(fetched) != 0:
        threadstatus = str(fetched[0][0])
        if threadstatus == "OK":
            Connection.Instance().cur.execute("UPDATE alerts set isalive = %s where alertid = %s;", [True, alertid])
            Connection.Instance().PostGreSQLConnect.commit()
            return {'message': "Your alert succesfully started!", 'type': 'success'}
        else:
            Connection.Instance().cur.execute("UPDATE alerts set isalive = %s where alertid = %s;", [False, alertid])
            Connection.Instance().PostGreSQLConnect.commit()
            return {'message': "Your alert could not start, please try again!", 'type': 'danger'}
    else:
        return {'message': "Your alert deleted", 'type': 'success'}

def getAllAlertList():
    Connection.Instance().cur.execute("Select * from alerts;")
    var = Connection.Instance().cur.fetchall()
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), \
               'lang': i[5].split(","), 'status': i[6], 'threadstatus': i[7], 'creationTime': i[8]} for i in var]
    alerts = sorted(alerts, key=lambda k: k['alertid'])
    return alerts

# Setups server
def setupServer():
    alerts = getAllAlertList()
    for alert in alerts:
        if alert['threadstatus'] == "OK":
            Connection.Instance().cur.execute("update alerts set isalive=%s where alertid = %s;", [True, alert['alertid']])
            Connection.Instance().PostGreSQLConnect.commit()
        else:
            Connection.Instance().cur.execute("update alerts set isalive=%s where alertid = %s;", [False, alert['alertid']])
            Connection.Instance().PostGreSQLConnect.commit()

# Refreshes Alerts status
def refrestAlertStatus(mainT):
    alerts = getAllAlertList()
    for alert in alerts:
        if alert['threadstatus'] == 'OK':
            aliveStatus = True
        else:
            aliveStatus = False
        Connection.Instance().cur.execute("update alerts set isalive=%s where alertid = %s;", [aliveStatus, alert['alertid']])
        Connection.Instance().PostGreSQLConnect.commit()

# Gives alerts as lists
def getAlertList(userid):
    Connection.Instance().cur.execute("Select * from alerts where userid = %s;", [userid])
    var = Connection.Instance().cur.fetchall()
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), 'lang': i[5].split(","),\
               'status': i[6], 'threadstatus': i[7], 'creationTime': i[8]} for i in var]
    alerts = sorted(alerts, key=lambda k: k['alertid'])
    for alert in alerts:
        alert['tweetCount'] = Connection.Instance().db[str(alert['alertid'])].find().count()
    return alerts

# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid != None:
        Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
        var = Connection.Instance().cur.fetchone()
        alert = {'alertid': var[0], 'name':var[2], 'keywords':var[3], 'lang': var[5].split(","), 'status': var[6], 'keywordlimit': var[9]}
    else:
        alert = {'alertid': "", 'name': "", 'keywords': "", 'lang': "", 'status': False, 'keywordlimit': 10}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    alert = {'alertid':var[0], 'name':var[2], 'keywords':var[3].split(","), 'lang': var[5].split(","), 'status': var[6]}
    return alert

# Give nextalertid
def getNextAlertId():
    Connection.Instance().cur.execute("select alertid from alerts order by alertid desc limit 1;")
    rows = Connection.Instance().cur.fetchall()
    if(len(rows) == 0):
        return 0
    else:
        for temp in rows:
            return temp[0]+1

def setUserAlertLimit(userid, setType):
    Connection.Instance().cur.execute("select alertlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    if setType == 'decrement':
        newLimit = fetched[0][0] - 1
    elif setType == 'increment':
        newLimit = fetched[0][0] + 1
    Connection.Instance().cur.execute("update users set alertlimit = %s where userid = %s", [newLimit, userid])
    Connection.Instance().PostGreSQLConnect.commit()

# Take alert information, give an id and add it DB
def addAlert(alert, mainT, userid):
    alert['alertid'] = getNextAlertId()
    now = strftime("%Y-%m-%d", gmtime())
    Connection.Instance().cur.execute("INSERT INTO alerts (alertid, userid, alertname, keywords, languages, creationtime, keywordlimit, threadstatus) values (%s, %s, %s, %s, %s, %s, %s, %s);", [alert['alertid'], userid, alert['name'], alert['keywords'], alert['lang'], now, alert['keywordlimit'], "OK"])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])
    setUserAlertLimit(userid, 'decrement')
    mainT.addAlert(alert)
    return response(alert['alertid'])

# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT, userid):
    alert = getAlertAllOfThemList(alertid)
    setUserAlertLimit(userid, 'increment')
    mainT.delAlert(alert)
    Connection.Instance().db[str(alertid)].drop()
    Connection.Instance().cur.execute("delete from alerts where alertid = %s;", [alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    return response(alertid)

# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT, userid):
    Connection.Instance().db[str(alert['alertid'])].drop()
    Connection.Instance().cur.execute("update alerts set userid = %s, keywords = %s , languages = %s, threadstatus = %s where alertid = %s;", [userid, alert['keywords'], alert['lang'], "OK", alert['alertid']])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])
    mainT.updateAlert(alert)
    return response(alert['alertid'])

# Starts alert streaming.
def startAlert(alertid, mainT):
    alert = getAlertAllOfThemList(alertid)
    mainT.addAlert(alert)
    return response(alert['alertid'])

# Stops alert streaming.
def stopAlert(alertid, mainT):
    Connection.Instance().cur.execute("update alerts set isalive = %s, threadstatus = %s where alertid = %s;", [False, '-', alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alertid)
    mainT.delAlert(alert)
    return response(alert['alertid'])

def getTweets(alertid):
    tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId' , pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
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
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
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
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
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
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
    return tweets
