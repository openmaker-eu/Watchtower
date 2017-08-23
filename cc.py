from newspaper import Article

from application.Connections import Connection

for i in Connection.Instance().newsPoolDB.collection_names():
    print(i)
    if i != "counters":
        for k in Connection.Instance().newsPoolDB[str(i)].find({}, {'url': 1}):
            published_at = None
            language = None
            try:
                article = Article(k['url'])
                article.build()

                published_at = article.publish_date
                language = article.meta_lang
            except Exception as e:
                pass

            Connection.Instance().newsPoolDB[str(i)].find_one_and_update({'_id': k['_id']}, \
                                                                         {'$set': {'published_at': published_at,
                                                                                   'language': language}})
