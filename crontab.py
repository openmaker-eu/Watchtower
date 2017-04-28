import pymongo
from application.Connections import Connection
import requests
import time

def determine_date(date):
    current_milli_time = int(round(time.time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'mouth':
        return str(current_milli_time - 30 * one_day)
    return '0'

def unshorten_url(url):
    return requests.head(url, allow_redirects=True).url

def calculateLinks(alertid, date):
    links = Connection.Instance().db[alertid].aggregate([{'$match': {'timestamp_ms': {'$gte': date} }},\
                                                         {'$unwind': "$entities.urls" },\
                                                         {'$group' : {'_id' :"$entities.urls.expanded_url" , 'total':{'$sum': 1}}},\
                                                         {'$sort': {'total': -1}}])
    links = list(links)
    result = []
    while result < 100 or links != []:
        link = links.pop()
        if link['_id'] != None:
            link = unshorten_url(link['_id'])
            if 'ebay' not in link:
                try:
                    g = Goose()
                    article = g.extract(url=link)
                    image = article.top_image.src
                    description = article.meta_description
                    if image and description:
                        result.append({'url': link, 'im':image, 'title': article.title.upper(), 'description': description})
                except Exception as e:
                    print e
                    pass
    return result

def main():
    userid = 4
    Connection.Instance().cur.execute("Select alertid from alerts where userid = %s;", [userid])
    alertid_list = list(Connection.Instance().cur.fetchall()[0])

    while alertid_list != []:
        alertid = alertid_list.pop()
        yesterday = calculateLinks(alertid, determine_date('yesterday'))
        if len(yesterday) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'yesterday'})
        else:
            Connection.Instance().newsdB[str(alertid)].insert_many({'name': 'yesterday', 'yesterday':yesterday})

        week = calculateLinks(alerid, determine_date('week'))
        if len(week) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'week'})
        else:
            Connection.Instance().newsdB[str(alertid)].insert_many({'name': 'week', 'week':week})

        month = calculateLinks(alertid, determine_date('month'))
        if len(month) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'month'})
        else:
            Connection.Instance().newsdB[str(alertid)].insert_many({'name': 'month', 'month':month})

        allofthem = calculateLinks(alertid, determine_date('all'))
        if len(allofthem) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'all'})
        else:
            Connection.Instance().newsdB[str(alertid)].insert_many({'name': 'all', 'all':allofthem})

if __name__ == '__main__':
    main()
