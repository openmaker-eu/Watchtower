from newspaper import Article
import pymongo
from application.Connections import Connection
from application.ThreadPool import ThreadPool
from requests import head
from time import gmtime, strftime, time
from urllib.parse import urlparse
from tldextract import extract
from queue import Queue
from threading import Thread
import timeout_decorator
from re import search, IGNORECASE

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

            if image != "" and description != "" and title != "":
                dic = {'url': link, 'im':image, 'title': title, 'description': description, 'keywords': keywords, 'popularity': int(count), 'source': source}
                return dic
    except Exception as e:
        print(e)
        pass

def calculateLinks(alertid):
    alertid = int(alertid)
    links = Connection.Instance().db[str(alertid)].aggregate([{'$match': {'timestamp_ms': {'$gte': date} }}, {'$unwind': "$entities.urls" }, \
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

def main():
    Connection.Instance().cur.execute("Select alertid from alerts;")
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    print(alertid_list)

    pool = ThreadPool(5)
    pool.map(calculateLinks, alertid_list)
    pool.wait_completion()

if __name__ == '__main__':
    main()
