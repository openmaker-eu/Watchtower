import sys
from time import gmtime, strftime, time

sys.path.append('./')
sys.path.insert(0,'/root/.local/share/virtualenvs/cloud-rP5jkfQF/lib/python3.5/site-packages/');

from application.Connections import Connection


def getDateList(alertid, date, forbidden_domain):
    return list(Connection.Instance().newsPoolDB[str(alertid)].aggregate([
        {'$project': {
            'link_id': 1,
            'published_at': {'$dateToString': {'format': "%d-%m-%Y", 'date': "$published_at"}},
            'source': 1,
            '_id': 0,
            'sentiment': 1,
            'im': 1,
            'url': 1,
            'full_text': 1,
            'summary': 1,
            'title': 1,
            'keywords': 1,
            'domain': 1,
            'bookmark': 1,
            'bookmark_date': 1,
            'mentions': {
                '$filter': {
                    'input': "$mentions",
                    'as': 'mention',
                    'cond': {
                        '$gte': [
                            '$$mention.timestamp_ms', date
                        ]
                    }
                }
            }
        }
        },
        {'$project': {
            'link_id': 1,
            'published_at': 1,
            'domain': 1,
            'source': 1,
            'sentiment': 1,
            '_id': 0,
            'im': 1,
            'url': 1,
            'full_text': 1,
            'summary': 1,
            'title': 1,
            'keywords': 1,
            'bookmark': 1,
            'bookmark_date': 1,
            'popularity': {'$size': '$mentions'}
        }},
        {'$match': {
            'popularity': {"$gt": 0},
            'domain': {'$nin': forbidden_domain}
        }},
        {'$sort': {'popularity': -1}},
        {'$limit': 60}
    ], allowDiskUse=True))


def calculate_dates():
    l = []
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    l.append(('yesterday', current_milli_time - one_day))
    l.append(('week', current_milli_time - 14 * one_day))
    l.append(('month', current_milli_time - 30 * one_day))
    return l


def calc(alertid, forbidden_domain):
    dates = calculate_dates()
    for date, current_milli_time in dates:
        result = {
            'name': date,
            date: getDateList(alertid, current_milli_time, forbidden_domain),
            'modified_date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())
        }
        if result[date] != []:
            Connection.Instance().filteredNewsPoolDB[str(alertid)].remove({'name': result['name']})
            Connection.Instance().filteredNewsPoolDB[str(alertid)].insert_one(result)


def main():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT user_id, ARRAY_agg(topic_id) as topics "
            "FROM user_topic "
            "GROUP BY user_id"
        )
        cur.execute(sql)
        user_topics = cur.fetchall()
        print(user_topics)
        for user_topic in user_topics:
            sql = (
                "SELECT ARRAY_agg(domain) as domains "
                "FROM user_domain "
                "WHERE user_id = %s "
                "GROUP BY user_id"
            )
            cur.execute(sql, [user_topic[0]])
            domains = cur.fetchone()
            if domains is not None:
                domains = domains[0]
            else:
                domains = []

            print(domains)
            for topic_id in user_topic[1]:
                calc(topic_id, domains)


if __name__ == '__main__':
    main()
