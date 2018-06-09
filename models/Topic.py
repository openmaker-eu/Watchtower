from application.Connections import Connection
from models.Model import Model


class Topic(Model):
    __slots__ = ['topic_id', 'topic_name', 'topic_description', 'keywords', 'languages', 'creation_time', 'type',
                 'keyword_limit', 'last_tweet_date', 'is_running', 'is_publish', 'last_news_date', 'is_masked_location',
                 'hash_tags', 'news_count', 'audience_count', 'event_count', 'tweet_count']

    keyword_num = 10

    @staticmethod
    def fields():
        return [
            'topic_id',
            'topic_name',
            'topic_description',
            'keywords',
            'languages',
            'creation_time',
            'keyword_limit',
            'last_tweet_date',
            'is_running',
            'is_publish',
            'last_news_date',
            'is_masked_location'
        ]

    @staticmethod
    def table_name():
        return "topics"

    @staticmethod
    def model_id_column():
        return "topic_id"

    @staticmethod
    def hidden_fields():
        pass

    # TODO: Change MongoDB calls
    def __getattribute__(self, item):
        if item in ['keywords', 'languages']:
            return object.__getattribute__(self, item).split(',')
        if item == 'keyword_limit':
            return self.keyword_num - len(self.keywords)
        if item == 'hash_tags':
            with Connection.Instance().get_cursor() as cur:
                try:
                    hash_tags = list(Connection.Instance().hashtags[
                        str(object.__getattribute__(self, self.model_id_column()))].find(
                        {'name': 'month'},
                        {'month': 1, 'count': 1,
                         '_id': 0}))[0]['month']
                except:
                    hash_tags = []
                    pass
                sql = (
                    "SELECT ARRAY_AGG(hashtag) FROM topic_hashtag WHERE topic_id = %s ;"
                )
                cur.execute(sql, [object.__getattribute__(self, self.model_id_column())])
                var = cur.fetchone()
                tags = var[0] if var[0] is not None else []
                return [
                    {'hashtag': hash_tag['hashtag'], 'count': hash_tag['count'],
                     'active': hash_tag['hashtag'] not in tags}
                    for hash_tag in hash_tags]
        if item == 'news_count':
            return Connection.Instance().newsPoolDB[
                str(object.__getattribute__(self, self.model_id_column()))].find().count()
        if item == 'audience_count':
            return Connection.Instance().audienceDB[
                str(object.__getattribute__(self, self.model_id_column()))].find().count()
        if item == 'event_count':
            return Connection.Instance().events[
                str(object.__getattribute__(self, self.model_id_column()))].find().count()
        if item == 'tweet_count':
            return Connection.Instance().db[
                str(object.__getattribute__(self, self.model_id_column()))].find().count()
        if item == 'type' and not hasattr(self, 'type'):
            return None
        return object.__getattribute__(self, item)

    def __init__(self, model):
        super().__init__(model)
