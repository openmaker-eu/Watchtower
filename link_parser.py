from newspaper import Article
from application.Connections import Connection
from application.ThreadPool import ThreadPool
from requests import head
from time import gmtime, strftime, time, sleep
from urllib.parse import urlparse
from tldextract import extract
import timeout_decorator
from re import search, IGNORECASE
import sys
from tldextract import extract

def get_next_links_sequence():
    cursor = Connection.Instance().newsPoolDB["counters"].find_and_modify(
            query= { '_id': "link_id" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

def unshorten_url(url):
    return head(url, allow_redirects=True).url

@timeout_decorator.timeout(4, use_signals=False)
def linkParser(link):
    try:
        parsed_uri = urlparse(link)
        source = '{uri.netloc}'.format(uri=parsed_uri)
        domain = extract(link).domain
        url = link
        article = Article(url)
        article.build()
        image = article.top_image
        keywords = article.keywords
        description = article.summary
        title = article.title
        if image != "" and description != "" and title != "":
            dic = {'url': link, 'im':image, 'title': title, 'domain': domain, 'description': description, 'keywords': keywords, 'source': source}
            print('done')
            return dic
    except Exception as e:
        pass

def calculateLinks(alertid, tweet):
    alertid = int(alertid)
    try:
        tweet_tuple = {'user_id': tweet['userid'], 'tweet_id': tweet['tweet_id'], 'timestamp_ms': int(tweet['timestamp_ms'])}
        for link in tweet['urls']:
            link = link['expanded_url']
            if link == None:
                continue
            if search('twitter', link):
                continue
            try:
                link = unshorten_url(link)
                if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'url':link}))) != 0:
                    Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'url': link}, {'$push': {'mentions': tweet_tuple}})
                    continue
                dic = linkParser(link)
                if dic != None:
                    if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'source':dic['source'], 'title':dic['title']}))) != 0:
                        Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'source':dic['source'], 'title':dic['title']}, {'$push': {'mentions': tweet_tuple}})
                    else:
                        dic['link_id'] = get_next_links_sequence()
                        dic['mentions']=[tweet_tuple]
                        Connection.Instance().newsPoolDB[str(alertid)].insert_one(dic)
            except Exception as e:
                print(link)
                print(e)
                pass
    except Exception as e:
        pass
