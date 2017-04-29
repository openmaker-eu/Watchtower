import pymongo
from application.Connections import Connection
import requests
import time
from goose import Goose
import resource

rsrc = resource.RLIMIT_DATA
soft, hard = resource.getrlimit(rsrc)
resource.setrlimit(rsrc, (512000000, hard)) #limit to one kilobyte

def determine_date(date):
    current_milli_time = int(round(time.time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'month':
        return str(current_milli_time - 30 * one_day)
    return '0'

def unshorten_url(url):
    return requests.head(url, allow_redirects=True).url

def calculateLinks(alertid, date):
    links = Connection.Instance().db[str(alertid)].aggregate([{'$match': {'timestamp_ms': {'$gte': date} }},\
                                                         {'$unwind': "$entities.urls" },\
                                                         {'$group' : {'_id' :"$entities.urls.expanded_url" , 'total':{'$sum': 1}}},\
                                                         {'$sort': {'total': -1}},\
                                                         {'$limit': 500}])
    links = list(links)
    result = []
    while len(result) < 100 and links != []:
        link = links.pop()
        if link['_id'] != None:
            try:
                link = unshorten_url(link['_id'])
                if 'ebay' not in link:
                    g = Goose()
                    article = g.extract(url=link)
                    image = article.top_image.src
                    description = article.meta_description
                    if image and description:
                        dic = {'url': link, 'im':image, 'title': article.title.upper(), 'description': description}
                        if dic not in result:
                            result.append(dic)
            except Exception as e:
                print e
                pass

    return result


userid = 4
Connection.Instance().cur.execute("Select alertid from alerts where userid = %s;", [userid])
alertid_list = list(Connection.Instance().cur.fetchall())
print alertid_list

while alertid_list != []:
    alertid = alertid_list.pop()[0]
    yesterday = calculateLinks(alertid, determine_date('yesterday'))
    if len(yesterday) != 0:
        Connection.Instance().newsdB[str(alertid)].remove({'name': 'yesterday'})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'yesterday', 'yesterday':yesterday})

    week = calculateLinks(alertid, determine_date('week'))
    if len(week) != 0:
        Connection.Instance().newsdB[str(alertid)].remove({'name': 'week'})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'week', 'week':week})

    month = calculateLinks(alertid, determine_date('month'))
    if len(month) != 0:
        Connection.Instance().newsdB[str(alertid)].remove({'name': 'month'})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'month', 'month':month})

    allofthem = calculateLinks(alertid, determine_date('all'))
    if len(allofthem) != 0:
        Connection.Instance().newsdB[str(alertid)].remove({'name': 'all'})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'all', 'all':allofthem})
