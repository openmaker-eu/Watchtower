from application.Connections import Connection


def clearNormalAccount():
    Connection.Instance().cur.execute("Select alertid from alerts where userid != %s;", [4])
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    alertid_list = [alertid[0] for alertid in alertid_list]
    for alertid in alertid_list:
        clear(alertid, 50000)


def clearOpenMakerUser():
    Connection.Instance().cur.execute("Select alertid from alerts where userid != %s;", [4])
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    alertid_list = [alertid[0] for alertid in alertid_list]
    for alertid in alertid_list:
        clear(alertid, 75000)


def clear(alertid, limit):
    current_count = Connection.Instance().db.command('collStats', str(alertid))['count']
    if current_count > limit:
        diff = current_count - limit
        tweetDBId = list(Connection.Instance().db[str(alertid)].find().skip(diff).limit(1))[0]['tweetDBId']
        Connection.Instance().db[str(alertid)].remove({'tweetDBId': {'$lte': tweetDBId}})


clearNormalAccount()
clearOpenMakerUser()
