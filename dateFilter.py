from application.Connections import Connection
from time import gmtime, strftime, time

def getDateList(alertid, date, forbidden_domain):
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
                'domain':1,
                'bookmark':1,
                'bookmark_date':1,
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
                'domain': 1,
                'source':1,
                '_id':0,
                'im':1,
                'url':1,
                'description':1,
                'title':1,
                'keywords':1,
                'bookmark':1,
                'bookmark_date':1,
                'popularity': {'$size': '$mentions'}
            }},
            {'$match': {
                'popularity' : {"$gt" : 0},
                'domain': {'$nin': forbidden_domain}
            }},
            {'$sort': {'popularity': -1}},
            {'$limit': 60}
    ]))

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
    Connection.Instance().cur.execute("Select alertid,domains from alerts;")
    alert_list = Connection.Instance().cur.fetchall()
    for alert in alert_list:
        calc(alert[0], alert[1].split(","))

if __name__ == '__main__':
    main()
