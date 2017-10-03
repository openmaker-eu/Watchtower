from application.Connections import Connection
from newspaper import Article

for topic_id in Connection.Instance().newsPoolDB.collection_names():
    if topic_id != "counters":
        for link in Connection.Instance().newsPoolDB[str(topic_id)].find({'full_text': {'$exists' : False}}, {'_id': 0, 'link_id':1, 'url':1}):
            article = Article(link['url'])
            try:
                article.download()
                article.parse()
            except:
                pass
            try:
                full_text = article.text
            except:
                full_text = None
                pass

            print(link['link_id'])
            Connection.Instance().newsPoolDB[str(topic_id)].find_one_and_update({'link_id': link['link_id']}, {
                '$set': {'full_text': full_text}})
