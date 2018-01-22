import sys
from time import gmtime, strftime, time

sys.path.insert(0,'/root/cloud')

from application.Connections import Connection


def getDateHashtags(alertid, date):
    return list(Connection.Instance().db[str(alertid)].aggregate([
        {
            '$match': {
                'timestamp_ms': {'$gte': str(date)}
            }
        },
        {
            '$unwind': '$entities.hashtags'
        },
        {
            '$project': {
                'hashtag': {
                    '$toLower': "$entities.hashtags.text"
                }
            },
        },
        {
            '$group': {
                '_id': '$hashtag',
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$project': {
                'count': 1,
                'hashtag': '$_id',
                '_id': 0
            }
        },
        {
            '$sort': {'count': -1}
        },
        {'$limit': 20}
    ]))


def calculate_dates():
    l = []
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    l.append(('yesterday', current_milli_time - one_day))
    l.append(('week', current_milli_time - 14 * one_day))
    l.append(('month', current_milli_time - 30 * one_day))
    return l


def calc(alertid):
    dates = calculate_dates()
    for date, current_milli_time in dates:
        result = {
            'name': date,
            date: getDateHashtags(alertid, current_milli_time),
            'modified_date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())
        }
        if result[date] != []:
            Connection.Instance().hashtags[str(alertid)].remove({'name': result['name']})
            Connection.Instance().hashtags[str(alertid)].insert_one(result)


if __name__ == '__main__':
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM topics"
        )
        cur.execute(sql)
        alert_list = cur.fetchall()
        for alert in alert_list:
            print(alert[0])
            calc(alert[0])
