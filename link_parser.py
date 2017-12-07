from urllib.parse import urlparse

from newspaper import Article
from requests import head
from tldextract import extract
import time, redis

# import application.utils.location.get_locations as get_location
import application.utils.dateExtractor as dateExtractor
import pymongo


def get_next_links_sequence(machine_host):
    MongoDBClient = pymongo.MongoClient('mongodb://admin:smio1EUp@'+machine_host+':27017/', connect=False)
    newsPoolDB = MongoDBClient.newsPool
    cursor = newsPoolDB["counters"].find_and_modify(
        query={'_id': "link_id"},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return cursor['seq']


def unshorten_url(url):
    return head(url, allow_redirects=True).url


def linkParser(link):
    redisConnection = redis.StrictRedis(host='localhost', port=6379, db=1)
    start_time = time.time()

    parsed_uri = urlparse(link)
    source = '{uri.netloc}'.format(uri=parsed_uri)
    domain = extract(link).domain

    delta = time.time() - start_time
    unshort_time = float(redisConnection.get('linkParser.getDomain'))
    unshort_time = unshort_time + delta
    redisConnection.set('linkParser.getDomain', unshort_time)

    start_time = time.time()

    article = Article(link)
    article.build()
    try:
        full_text = article.text
    except:
        full_text = None
        pass

    image = article.top_image
    keywords = article.keywords
    summary = article.summary
    title = article.title

    delta = time.time() - start_time
    unshort_time = float(redisConnection.get('linkParser.parseArticle'))
    unshort_time = unshort_time + delta
    redisConnection.set('linkParser.parseArticle', unshort_time)

    start_time = time.time()

    try:
        published_at = dateExtractor.extractArticlePublishedDate(link)
    except Exception as e:
        published_at = None
        print(e)
        print("\n\n\n")
        pass

    delta = time.time() - start_time
    unshort_time = float(redisConnection.get('linkParser.getDate'))
    unshort_time = unshort_time + delta
    redisConnection.set('linkParser.getDate', unshort_time)

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

    """
    places = get_location.get_place_context(text=description)

    location = {
        "countries": places.countries,
        "country_mentions" : places.country_mentions,
        "cities" : places.cities,
        "city_mentions" : places.city_mentions
    }
    """

    if image != "" and full_text != "" and title != "":
        dic = {'url': link, 'im': image, 'title': title, 'domain': domain, 'full_text': full_text,
               'summary': summary, 'keywords': keywords, 'source': source,
               'published_at': published_at, 'language': language, 'author': author}
        print('done')
        return dic


def calculateLinks(data, machine_host):
    redisConnection = redis.StrictRedis(host='localhost', port=6379, db=1)
    MongoDBClient = pymongo.MongoClient('mongodb://admin:smio1EUp@'+machine_host+':27017/', connect=False)
    newsPoolDB = MongoDBClient.newsPool
    if data['channel'] == 'reddit':
        link = data['url']
        topic_id = data['topic_id']

        try:
            start_time = time.time()

            link = unshorten_url(link)

            delta = time.time() - start_time
            unshort_time = float(redisConnection.get('unshort'))
            unshort_time = unshort_time + delta
            redisConnection.set('unshort', unshort_time)

            start_time = time.time()

            check = len(list(newsPoolDB[str(topic_id)].find({'url': link})))

            delta = time.time() - start_time
            unshort_time = float(redisConnection.get('search_link_db'))
            unshort_time = unshort_time + delta
            redisConnection.set('search_link_db', unshort_time)

            if check != 0:
                start_time = time.time()

                newsPoolDB[str(topic_id)].find_one_and_update({'url': link}, {
                    '$addToSet': {'mentions': {'$each': data['mentions']}}})

                delta = time.time() - start_time
                unshort_time = float(redisConnection.get('search_link_db_update'))
                unshort_time = unshort_time + delta
                redisConnection.set('search_link_db_update', unshort_time)
            else:
                start_time = time.time()

                dic = linkParser(link)

                delta = time.time() - start_time
                unshort_time = float(redisConnection.get('link_parser'))
                unshort_time = unshort_time + delta
                redisConnection.set('link_parser', unshort_time)

                if dic is not None:

                    start_time = time.time()

                    check = len(list(newsPoolDB[str(topic_id)].find(
                            {'domain': dic['domain'], 'title': dic['title']})))

                    delta = time.time() - start_time
                    unshort_time = float(redisConnection.get('search_duplicate_link'))
                    unshort_time = unshort_time + delta
                    redisConnection.set('search_duplicate_link', unshort_time)

                    if check != 0:
                        start_time = time.time()

                        newsPoolDB[str(topic_id)] \
                            .find_one_and_update(
                            {'source': dic['source'], 'title': dic['title']},
                            {'$addToSet': {'mentions': {'$each': data['mentions']}},
                             '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                      'author': dic['author']}})

                        delta = time.time() - start_time
                        unshort_time = float(redisConnection.get('search_duplicate_link_update'))
                        unshort_time = unshort_time + delta
                        redisConnection.set('search_duplicate_link_update', unshort_time)

                    else:
                        dic['link_id'] = get_next_links_sequence(machine_host)
                        dic['mentions'] = data['mentions']
                        newsPoolDB[str(topic_id)].insert_one(dic)
        except Exception as e:
            print(e)
            pass
    elif data['channel'] == 'facebook':
        short_link = data['url']
        topic_id = data['topic_id']

        try:
            start_time = time.time()

            link = unshorten_url(link)

            delta = time.time() - start_time
            unshort_time = float(redisConnection.get('unshort'))
            unshort_time = unshort_time + delta
            redisConnection.set('unshort', unshort_time)

            start_time = time.time()

            check = len(list(newsPoolDB[str(topic_id)].find({'url': link})))

            delta = time.time() - start_time
            unshort_time = float(redisConnection.get('search_link_db'))
            unshort_time = unshort_time + delta
            redisConnection.set('search_link_db', unshort_time)

            if check != 0:
                start_time = time.time()

                newsPoolDB[str(topic_id)].find_one_and_update({'url': link}, {
                    '$addToSet': {'mentions': {'$each': data['mentions']}}})

                delta = time.time() - start_time
                unshort_time = float(redisConnection.get('search_link_db_update'))
                unshort_time = unshort_time + delta
                redisConnection.set('search_link_db_update', unshort_time)
                return

            start_time = time.time()

            check = len(list(newsPoolDB[str(topic_id)].find(
                    {'short_links': short_link})))

            delta = time.time() - start_time
            unshort_time = float(redisConnection.get('search_shortlink_db'))
            unshort_time = unshort_time + delta
            redisConnection.set('search_shortlink_db', unshort_time)

            if check != 0:
                start_time = time.time()

                newsPoolDB[str(topic_id)].find_one_and_update(
                    {'short_links': short_link}, {'$addToSet': {'mentions': {'$each': data['mentions']}}})

                delta = time.time() - start_time
                unshort_time = float(redisConnection.get('search_shortlink_db_update'))
                unshort_time = unshort_time + delta
                redisConnection.set('search_shortlink_db_update', unshort_time)
            else:
                start_time = time.time()

                dic = linkParser(link)

                delta = time.time() - start_time
                unshort_time = float(redisConnection.get('link_parser'))
                unshort_time = unshort_time + delta
                redisConnection.set('link_parser', unshort_time)
                if dic is not None:
                    start_time = time.time()

                    check = len(list(newsPoolDB[str(topic_id)].find(
                            {'domain': dic['domain'], 'title': dic['title']})))

                    delta = time.time() - start_time
                    unshort_time = float(redisConnection.get('search_duplicate_link'))
                    unshort_time = unshort_time + delta
                    redisConnection.set('search_duplicate_link', unshort_time)

                    if check != 0:
                        start_time = time.time()

                        newsPoolDB[str(topic_id)] \
                            .find_one_and_update(
                            {'source': dic['source'], 'title': dic['title']},
                            {'$addToSet': {'mentions': {'$each': data['mentions']}},
                             '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                      'author': dic['author']}})

                        delta = time.time() - start_time
                        unshort_time = float(redisConnection.get('search_duplicate_link_update'))
                        unshort_time = unshort_time + delta
                        redisConnection.set('search_duplicate_link_update', unshort_time)

                    else:
                        dic['link_id'] = get_next_links_sequence(machine_host)
                        dic['mentions'] = data['mentions']
                        dic['short_links'] = [short_link]
                        newsPoolDB[str(topic_id)].insert_one(dic)
        except Exception as e:
            print(e)
            pass
    else:
        topic_id = data['alertid']
        tweet = data['tweet']
        print("processing...")
        topic_id = int(topic_id)
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

                    start_time = time.time()

                    link = unshorten_url(link)

                    delta = time.time() - start_time
                    unshort_time = float(redisConnection.get('unshort'))
                    unshort_time = unshort_time + delta
                    redisConnection.set('unshort', unshort_time)

                    start_time = time.time()

                    check = len(list(newsPoolDB[str(topic_id)].find({'url': link})))

                    delta = time.time() - start_time
                    unshort_time = float(redisConnection.get('search_link_db'))
                    unshort_time = unshort_time + delta
                    redisConnection.set('search_link_db', unshort_time)

                    if check != 0:
                        start_time = time.time()

                        newsPoolDB[str(topic_id)].find_one_and_update({'url': link}, {
                            '$addToSet': {'mentions': {'$each': data['mentions']}}})

                        delta = time.time() - start_time
                        unshort_time = float(redisConnection.get('search_link_db_update'))
                        unshort_time = unshort_time + delta
                        redisConnection.set('search_link_db_update', unshort_time)
                        return

                    start_time = time.time()

                    check = len(list(newsPoolDB[str(topic_id)].find(
                            {'short_links': short_link})))

                    delta = time.time() - start_time
                    unshort_time = float(redisConnection.get('search_shortlink_db'))
                    unshort_time = unshort_time + delta
                    redisConnection.set('search_shortlink_db', unshort_time)

                    if check != 0:
                        start_time = time.time()

                        newsPoolDB[str(topic_id)].find_one_and_update(
                            {'short_links': short_link}, {'$addToSet': {'mentions': {'$each': data['mentions']}}})

                        delta = time.time() - start_time
                        unshort_time = float(redisConnection.get('search_shortlink_db_update'))
                        unshort_time = unshort_time + delta
                        redisConnection.set('search_shortlink_db_update', unshort_time)
                    else:
                        start_time = time.time()

                        dic = linkParser(link)

                        delta = time.time() - start_time
                        unshort_time = float(redisConnection.get('link_parser'))
                        unshort_time = unshort_time + delta
                        redisConnection.set('link_parser', unshort_time)
                        if dic is not None:
                            start_time = time.time()

                            check = len(list(newsPoolDB[str(topic_id)].find(
                                    {'domain': dic['domain'], 'title': dic['title']})))

                            delta = time.time() - start_time
                            unshort_time = float(redisConnection.get('search_duplicate_link'))
                            unshort_time = unshort_time + delta
                            redisConnection.set('search_duplicate_link', unshort_time)

                            if check != 0:
                                start_time = time.time()

                                newsPoolDB[str(topic_id)] \
                                    .find_one_and_update(
                                    {'source': dic['source'], 'title': dic['title']},
                                    {'$addToSet': {'mentions': {'$each': data['mentions']}},
                                     '$set': {'published_at': dic['published_at'], 'language': dic['language'],
                                              'author': dic['author']}})

                                delta = time.time() - start_time
                                unshort_time = float(redisConnection.get('search_duplicate_link_update'))
                                unshort_time = unshort_time + delta
                                redisConnection.set('search_duplicate_link_update', unshort_time)
                            else:
                                dic['link_id'] = get_next_links_sequence(machine_host)
                                dic['mentions'] = [tweet_tuple]
                                dic['short_links'] = [short_link]
                                newsPoolDB[str(topic_id)].insert_one(dic)
                except Exception as e:
                    print(e)
                    pass
        except Exception as e:
            print(e)
            pass
