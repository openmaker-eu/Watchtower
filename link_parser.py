from urllib.parse import urlparse

from newspaper import Article
from requests import head
from tldextract import extract

# import application.utils.location.get_locations as get_location
import application.utils.dateExtractor as dateExtractor
from application.Connections import Connection


def get_next_links_sequence():
    cursor = Connection.Instance().newsPoolDB["counters"].find_and_modify(
        query={'_id': "link_id"},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return cursor['seq']


def unshorten_url(url):
    return head(url, allow_redirects=True).url


def linkParser(link):
    parsed_uri = urlparse(link)
    source = '{uri.netloc}'.format(uri=parsed_uri)
    domain = extract(link).domain
    article = Article(link)
    article.build()
    image = article.top_image
    keywords = article.keywords
    description = article.summary
    title = article.title

    try:
        published_at = dateExtractor.extractArticlePublishedDate(link)
    except Exception as e:
        published_at = None
        print(e)
        print("\n\n\n")
        pass

    try:
        language = article.meta_lang
    except:
        language = None
        pass

    try:
        author = article.authors
    except:
        author = None
        pass

    """places = get_location.get_place_context(text=description)

    location = {
        "countries": places.countries,
        "country_mentions" : places.country_mentions,
        "cities" : places.cities,
        "city_mentions" : places.city_mentions
    }
"""
    if image != "" and description != "" and title != "":
        dic = {'url': link, 'im': image, 'title': title, 'domain': domain,
               'description': description, 'keywords': keywords, 'source': source,
               'published_at': published_at, 'language': language, 'author': author}
        print('done')
        return dic


def calculateLinks(data):
    if data['channel'] == 'reddit':
        link = data['url']
        topic_id = data['topic_id']

        try:
            link = unshorten_url(link)
            if len(list(Connection.Instance().newsPoolDB[str(topic_id)].find({'url': link}))) != 0:
                print("found in db")
                Connection.Instance().newsPoolDB[str(topic_id)].find_one_and_update({'url': link}, {
                    '$push': {'mentions': {'$each': data['mentions']}}})

            dic = linkParser(link)
            if dic is not None:
                if len(list(Connection.Instance().newsPoolDB[str(topic_id)].find(
                        {'domain': dic['domain'], 'title': dic['title']}))) != 0:
                    Connection.Instance().newsPoolDB[str(topic_id)] \
                        .find_one_and_update(
                        {'source': dic['source'], 'title': dic['title']},
                        {'$push': {'mentions': {'$each': data['mentions']}},
                         '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                  'author': dic['author']}})
                else:
                    dic['link_id'] = get_next_links_sequence()
                    dic['mentions'] = data['mentions']
                    dic['forbidden'] = False
                    dic['bookmark'] = False
                    dic['bookmark_date'] = None
                    Connection.Instance().newsPoolDB[str(topic_id)].insert_one(dic)
        except Exception as e:
            print(link)
            print(e)
            pass
    elif data['channel'] == 'facebook':
        short_link = data['url']
        topic_id = data['topic_id']
        link = unshorten_url(short_link)

        try:
            if len(list(Connection.Instance().newsPoolDB[str(topic_id)].find({'url': link}))) != 0:
                Connection.Instance().newsPoolDB[str(topic_id)].find_one_and_update({'url': link}, {
                    '$push': {'mentions': {'$each': data['mentions']}}})

            if len(list(Connection.Instance().newsPoolDB[str(topic_id)].find(
                    {'short_links': short_link}))) != 0:
                Connection.Instance().newsPoolDB[str(topic_id)].find_one_and_update(
                    {'short_links': short_link}, {'$push': {'mentions': {'$each': data['mentions']}}})
                print('short_link : ' , short_link)

            dic = linkParser(link)
            if dic is not None:
                if len(list(Connection.Instance().newsPoolDB[str(topic_id)].find(
                        {'domain': dic['domain'], 'title': dic['title']}))) != 0:
                    Connection.Instance().newsPoolDB[str(topic_id)] \
                        .find_one_and_update(
                        {'source': dic['source'], 'title': dic['title']},
                        {'$push': {'mentions': {'$each': data['mentions']}},
                         '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                  'author': dic['author']}, '$addToSet': {'short_links': short_link}})
                else:
                    dic['link_id'] = get_next_links_sequence()
                    dic['mentions'] = data['mentions']
                    dic['forbidden'] = False
                    dic['bookmark'] = False
                    dic['bookmark_date'] = None
                    dic['short_links'] = [short_link]
                    Connection.Instance().newsPoolDB[str(topic_id)].insert_one(dic)
        except Exception as e:
            print(link)
            print(e)
            pass
    else:
        alertid = data['alertid']
        tweet = data['tweet']
        print("processing...")
        alertid = int(alertid)
        try:
            lang = None
            location = None

            try:
                lang = tweet['user']['lang']
                location = tweet['user']['location']
            except:
                pass

            tweet_tuple = {'user_id': tweet['user']['id_str'], 'tweet_id': tweet['id_str'],
                           'timestamp_ms': int(tweet['timestamp_ms']), 'language': lang, 'location': location}
            for link in tweet['entities']['urls']:
                link = link['expanded_url']
                if link is None:
                    continue
                try:
                    short_link = link
                    link = unshorten_url(link)
                    if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'url': link}))) != 0:
                        Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'url': link}, {
                            '$push': {'mentions': tweet_tuple}})
                        continue
                    if len(list(Connection.Instance().newsPoolDB[str(alertid)].find(
                            {'short_links': short_link}))) != 0:
                        Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update(
                            {'short_links': short_link}, {'$push': {'mentions': tweet_tuple}})
                        print('short_link : ' , short_link)
                        continue
                    dic = linkParser(link)
                    if dic is not None:
                        if len(list(Connection.Instance().newsPoolDB[str(alertid)].find(
                                {'domain': dic['domain'], 'title': dic['title']}))) != 0:
                            Connection.Instance().newsPoolDB[str(alertid)] \
                                .find_one_and_update(
                                {'source': dic['source'], 'title': dic['title']},
                                {'$push': {'mentions': tweet_tuple},
                                 '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                          'author': dic['author']}, '$addToSet': {'short_links': short_link}})
                        else:
                            dic['link_id'] = get_next_links_sequence()
                            dic['mentions'] = [tweet_tuple]
                            dic['forbidden'] = False
                            dic['bookmark'] = False
                            dic['bookmark_date'] = None
                            dic['short_links'] = [short_link]
                            Connection.Instance().newsPoolDB[str(alertid)].insert_one(dic)
                except Exception as e:
                    print(link)
                    print(e)
                    pass
        except Exception as e:
            print(e)
            pass


def createParameters(alertid, tweets):
    return [[alertid, tweet] for tweet in tweets]
