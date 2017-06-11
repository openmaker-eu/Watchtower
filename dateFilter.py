from application.Connections import Connection
from time import gmtime, strftime, time

def getDateList(alertid, date):
    return list(Connection.Instance().newsPoolDB[str(alertid)].aggregate([
        {'$project': {
                'link_id':1,
                'source':1,
                '_id':0,
                'im':1,
                'url':1,
                'description':1,
                'title':1,
                'keywords':1,
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
                'link_id':1,
                'source':1,
                '_id':0,
                'im':1,
                'url':1,
                'description':1,
                'title':1,
                'keywords':1,
                'popularity': {'$size': '$mentions'}
            }},
        {'$sort': {'popularity': -1}},
        {'$limit': 60}
    ]))

def calculate_dates():
    l = []
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    l.append(('yesterday', current_milli_time - one_day))
    l.append(('week', current_milli_time - 7 * one_day))
    l.append(('month', current_milli_time - 30 * one_day))
    return l

def calc(alertid, dates):
    for date, current_milli_time in dates:
        result = {
            'name': date,
            date: getDateList(alertid, current_milli_time),
            'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())
        }
        Connection.Instance().filteredNewsPoolDB[str(alertid)].insert_one(result)

def main():
    dates = calculate_dates()
    for alertid in Connection.Instance().db.collection_names():
        if alertid != u'counters':
            calc(alertid, dates)

if __name__ == '__main__':
    main()
