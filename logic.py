import re
import search
import pymongo
from application.Connections import Connection
from time import gmtime, strftime
import sys
reload(sys)
sys.setdefaultencoding('utf8')

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
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), 'excludedkeywords': i[4].split(","),\
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
    threadDict = mainT.getThreadDic()
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
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), 'excludedkeywords': i[4].split(","),\
               'lang': i[5].split(","), 'status': i[6], 'threadstatus': i[7], 'creationTime': i[8]} for i in var]
    alerts = sorted(alerts, key=lambda k: k['alertid'])
    return alerts

# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid != None:
        Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
        var = Connection.Instance().cur.fetchone()
        alert = {'alertid': var[0], 'name':var[2], 'keywords':var[3], 'excludedkeywords': var[4], 'lang': var[5].split(","), 'status': var[6]}
    else:
        alert = {'alertid': "", 'name': "", 'keywords': "", 'excludedkeywords': "", 'lang': "", 'status': False}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    alert = {'alertid':var[0], 'name':var[2], 'keywords':var[3].split(","), 'excludedkeywords':var[4].split(","), 'lang': var[5].split(","), 'status': var[6]}
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

# Take alert information, give an id and add it DB
def addAlert(alert, mainT, userid):
    alert['alertid'] = getNextAlertId()
    now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    Connection.Instance().cur.execute("INSERT INTO alerts (alertid, userid, alertname, keywords,excludedkeywords, languages, creationtime) values (%s, %s, %s, %s, %s, %s, %s);", [alert['alertid'], userid, alert['name'], alert['keywords'], alert['excludedkeywords'], alert['lang'], now])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])

    length = len(alert['keywords'])
    Connection.Instance().cur.execute("select keywordlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    newLimit = fetched[0][0] - length
    Connection.Instance().cur.execute("update users set keywordlimit = %s where userid = %s", [newLimit, userid])
    Connection.Instance().PostGreSQLConnect.commit()

    mainT.addThread(alert)
    return response(alert['alertid'])


# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT, userid):
    if str(alert['alertid']) in mainT.getThreadDic():
        mainT.killThread(alert)

    oldNumOfKeywords = len(getAlertAllOfThemList(alert['alertid'])['keywords'])

    Connection.Instance().db[str(alert['alertid'])].drop()
    Connection.Instance().cur.execute("update alerts set userid = %s, keywords = %s ,excludedkeywords = %s, languages = %s where alertid = %s;", [userid, alert['keywords'],alert['excludedkeywords'], alert['lang'], alert['alertid']])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])

    length = len(alert['keywords'])
    Connection.Instance().cur.execute("select keywordlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    newLimit = fetched[0][0] - (length - oldNumOfKeywords)
    Connection.Instance().cur.execute("update users set keywordlimit = %s where userid = %s", [newLimit, userid])
    Connection.Instance().PostGreSQLConnect.commit()

    mainT.addThread(alert)
    return response(alert['alertid'])

# Starts alert streaming.
def startAlert(alertid, mainT):
    alert = getAlertAllOfThemList(alertid)
    mainT.addThread(alert)
    return response(alert['alertid'])

# Stops alert streaming.
def stopAlert(alertid, mainT):
    Connection.Instance().cur.execute("update alerts set isalive = %s where alertid = %s;", [False, alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alertid)
    print mainT.getThreadDic(), alert['alertid']
    if str(alert['alertid']) in mainT.getThreadDic():
        mainT.killThread(alert)
    return response(alert['alertid'])

# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT, userid):
    alert = getAlertAllOfThemList(alertid)

    oldNumOfKeywords = len(getAlertAllOfThemList(alert['alertid'])['keywords'])
    length = len(alert['keywords'])
    Connection.Instance().cur.execute("select keywordlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    newLimit = fetched[0][0] + oldNumOfKeywords
    Connection.Instance().cur.execute("update users set keywordlimit = %s where userid = %s", [newLimit, userid])
    Connection.Instance().PostGreSQLConnect.commit()

    if str(alert['alertid']) in mainT.getThreadDic():
        print "delete"
        mainT.killThread(alert)
        print mainT.getThreadDic()
    Connection.Instance().db[str(alertid)].drop()
    Connection.Instance().cur.execute("delete from alerts where alertid = %s;", [alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    return response(alertid)

def getTweets(alertid):
    tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId' , pymongo.DESCENDING)]).limit(25)
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
