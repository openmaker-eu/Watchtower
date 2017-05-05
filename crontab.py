import pymongo
from application.Connections import Connection
import requests
import time
import summary
from goose import Goose
import resource
from time import gmtime, strftime
from urlparse import urlparse

g = Goose({'browser_user_agent': 'Mozilla', 'parser_class':'lxml'})
rsrc = resource.RLIMIT_DATA
soft, hard = resource.getrlimit(rsrc)
resource.setrlimit(rsrc, (512000000, hard)) #limit to one 512mb
unwanted_links = ['ebay', 'gearbest', 'abizy']

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
    while len(result) < 60 and links != []:
        link = links.pop(0)
        if link['_id'] != None:
            try:
                count = link['total']
                link = unshorten_url(link['_id'])
                parsed_uri = urlparse(link)
                domain = parsed_uri.netloc[:parsed_uri.netloc.index(".")]
                if domain not in unwanted_links:
                    source = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                    #article = g.extract(url=link)
                    #image = article.top_image.src
                    #description = article.meta_description
                    #title = article.title.upper()
                    s = summary.Summary(link)
                    s.extract()
                    image = str(s.image).encode('utf-8')
                    title = str(s.title.encode('utf-8'))
                    description = str(s.description.encode('utf-8'))
                    if image != "None" and description != "None":
                        dic = {'url': link, 'im':image, 'title': title, 'description': description, 'popularity': int(count), 'source': source}
                        if not next((item for item in result if item["title"] == dic['title'] and item["im"] == dic['im']\
                         and item["description"] == dic['description']), False):
                            result.append(dic)
            except Exception as e:
                pass
    return result

def main():
    Connection.Instance().cur.execute("Select alertid from alerts where userid = %s;", [4])
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    print alertid_list

    while alertid_list != []:
        alertid = alertid_list.pop(0)[0]
        yesterday = calculateLinks(alertid, determine_date('yesterday'))
        if len(yesterday) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'yesterday'})
            Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'yesterday', 'yesterday':yesterday, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})

        week = calculateLinks(alertid, determine_date('week'))
        if len(week) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'week'})
            Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'week', 'week':week, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})

        month = calculateLinks(alertid, determine_date('month'))
        if len(month) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'month'})
            Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'month', 'month':month, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})

        print alertid, "fetched!"
    """
        allofthem = calculateLinks(alertid, determine_date('all'))
        if len(allofthem) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'all'})
            Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'all', 'all':allofthem, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})
    """
if __name__ == '__main__':
    main()
