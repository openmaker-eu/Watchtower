from newspaper import Article
import pymongo
from application.Connections import Connection
from application.ThreadPool import ThreadPool
from requests import head
from time import gmtime, strftime, time, sleep
from urllib.parse import urlparse
from tldextract import extract
import timeout_decorator
from re import search, IGNORECASE

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

@timeout_decorator.timeout(15, use_signals=True)
def linkParser(link):
    try:
        parsed_uri = urlparse(link)
        source = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        url = link
        article = Article(url)
        article.download()
        sleep(1)
        article.parse()
        image = article.top_image

        article.nlp()
        keywords = article.keywords
        description = article.summary
        title = article.title

        if search(r"javascript is disabled error", description, IGNORECASE):
            raise Exception("java script")

        if image != "" and description != "" and title != "":
            dic = {'url': link, 'im':image, 'title': title, 'description': description, 'keywords': keywords, 'source': source}
            return dic
    except Exception as e:
        print(e, '____parser_____')
        pass

def calculateLinks(alertid):
    alertid = int(alertid)
    for tweet in Connection.Instance().db[str(alertid)].find({'isClicked': False}):
        Connection.Instance().db[str(alertid)].find_one_and_update({'id':tweet['id']}, {'$set': {'isClicked': True}})
        tweet_tuple = {'user_id': tweet['user']['id_str'], 'tweet_id': tweet['id_str'], 'timestamp_ms': int(tweet['timestamp_ms'])}
        for link in tweet['entities']['urls']:
            link = link['expanded_url']
            if link == None:
                continue
            try:
                link = unshorten_url(link)
                dic = linkParser(link)
                if dic != None:
                    if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'source':dic['source'], 'title':dic['title']}))) == 0:
                        dic['link_id'] = get_next_links_sequence()
                        dic['mentions']=[tweet_tuple]
                        Connection.Instance().newsPoolDB[str(alertid)].insert_one(dic)
                    else:
                        Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'source':dic['source'], 'title':dic['title']}, {'$push': {'mentions': tweet_tuple}})
            except Exception as e:
                print('link: ', link)
                print(e, '_____calculate_____')
                pass

def main():
    calculateLinks(31)

if __name__ == '__main__':
    main()
