import sys
from time import gmtime, strftime, time
import datetime
from decouple import config

sys.path.insert(0, config("ROOT_DIR"))

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
        {'$limit': 50}
    ]))



def calc(alertid):
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000

    result = {
        'hashtag': getDateHashtags(alertid, current_milli_time - one_day),
        'modified_date': datetime.datetime.now()
    }

    Connection.Instance().daily_hastags[str(alertid)].insert_one(result)


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
