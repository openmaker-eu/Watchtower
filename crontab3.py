from newspaper import Article
import pymongo
from application.Connections import Connection
from application.ThreadPool import ThreadPool
#from application.TimeOut import timeout
from requests import head
from time import gmtime, strftime, time
from urllib.parse import urlparse
from tldextract import extract
import timeout_decorator
from re import search, IGNORECASE

unwanted_links = ['ebay', 'gearbest', 'abizy', 'twitter', 'facebook', 'swarmapp']

def determine_date(date):
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'month':
        return str(current_milli_time - 30 * one_day)
    return '0'

def unshorten_url(url):
    return head(url, allow_redirects=True).url

@timeout_decorator.timeout(15, use_signals=False)
def linkParser(link):
    print("working")
    try:
        count = link['total']
        link = unshorten_url(link['_id'])
        parsed_uri = urlparse(link)
        domain = extract(link).domain
        if domain not in unwanted_links:
            source = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

            url = link
            article = Article(url)
            article.download()
            article.parse()
            image = article.top_image

            article.nlp()
            keywords = article.keywords
            description = article.summary
            title = article.title

            if search(r"javascript is disabled error", description, IGNORECASE):
                raise Exception("java script")

            #g = Goose({'browser_user_agent': 'Mozilla', 'parser_class':'lxml'})
            #article = g.extract(url=link)
            #image = str(article.top_image.src)
            #description = str(article.meta_description)
            #title = article.title.upper()

            #s = summary.Summary(link)
            #s.extract()
            #image = str(s.image).encode('utf-8')
            #title = str(s.title.encode('utf-8'))
            #description = str(s.description.encode('utf-8'))

            if image != "" and description != "" and title != "":
                dic = {'url': link, 'im':image, 'title': title, 'description': description, 'keywords': keywords, 'popularity': int(count), 'source': source}
                return dic
    except Exception as e:
        print(e)
        pass

def calculateLinks(alertid, date):
    print(alertid, date)
    stringDate = date
    date = determine_date(date)
    links = Connection.Instance().db[str(alertid)].aggregate([{'$match': {'timestamp_ms': {'$gte': date} }},\
                                                         {'$unwind': "$entities.urls" },\
                                                         {'$group' : {'_id' :"$entities.urls.expanded_url" , 'total':{'$sum': 1}}},\
                                                         {'$sort': {'total': -1}},\
                                                         {'$limit': 500}])

    links = list(links)
    result = []
    while len(result) < 60 and links != []:
        print(len(result))
        link = links.pop(0)
        if link['_id'] != None:
            try:
                dic = linkParser(link)
                if dic != None and not next((item for item in result if item["title"] == dic['title'] and item["im"] == dic['im']\
                 and item["description"] == dic['description']), False):
                    result.append(dic)
            except:
                pass

    if result != []:
        Connection.Instance().newsdB[str(alertid)].remove({'name': stringDate})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': stringDate, stringDate:result, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})


def createParameters(alertid_list):
    dates = ['yesterday', 'week', 'month']
    return [[alertid[0],date] for alertid in alertid_list for date in dates]

def main():
    Connection.Instance().cur.execute("Select alertid from alerts;")
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    parameters = createParameters(alertid_list)
    alertid_list = [31,32,33]
    dates = ['yesterday', 'week', 'month']
    parameters = [[alert, date] for alert in alertid_list for date in dates]
    print(alertid_list)
    pool = ThreadPool(1,True)
    pool.map(calculateLinks, parameters)
    pool.wait_completion()

"""
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


        allofthem = calculateLinks(alertid, determine_date('all'))
        if len(allofthem) != 0:
            Connection.Instance().newsdB[str(alertid)].remove({'name': 'all'})
            Connection.Instance().newsdB[str(alertid)].insert_one({'name': 'all', 'all':allofthem, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})
    """
if __name__ == '__main__':
    main()
