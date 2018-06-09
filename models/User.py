from models.Model import Model
from models.Topic import Topic as Topic


class User(Model):
    __slots__ = ['user_id', 'username', 'password', 'topic_limit', 'current_topic_id', 'country_code',
                 'country_location', 'twitter_access_token', 'twitter_access_secret']

    @staticmethod
    def fields():
        return [
            'user_id',
            'username',
            'password',
            'topic_limit',
            'current_topic_id',
            'country_code',
            'country_location',
            'twitter_access_token',
            'twitter_access_secret'
        ]

    @staticmethod
    def table_name():
        return "users"

    @staticmethod
    def model_id_column():
        return "user_id"

    @staticmethod
    def hidden_fields():
        return ['password']

    def __init__(self, model):
        super().__init__(model)

    def attach_topic(self, topic_id):
        self.add_relation('user_topic', 'topic_id', topic_id)

    def detach_topic(self, topic_id):
        self.delete_relation('user_topic', 'topic_id', topic_id)

    def subscribe_topic(self, topic_id):
        self.add_relation('user_topic_subscribe', 'topic_id', topic_id)

    def unsubscribe_topic(self, topic_id):
        self.delete_relation('user_topic_subscribe', 'topic_id', topic_id)

    def own_topics(self):
        topic_ids = self.get_relations('user_topic', 'topic_id')
        topics = Topic.find_all([('topic_id', 'IN', tuple(topic_ids))]) if len(topic_ids) > 0 else []
        return_topics = []
        for i in topics:
            i.__setattr__('type', 'me')
            return_topics.append(i)
        return return_topics

    def subscribe_topics(self):
        topic_ids = self.get_relations('user_topic_subscribe', 'topic_id')
        topics = Topic.find_all([('topic_id', 'IN', tuple(topic_ids))]) if len(topic_ids) > 0 else []
        return_topics = []
        for i in topics:
            i.__setattr__('type', 'subscribed')
            return_topics.append(i)
        return return_topics

    def unsubscribe_topics(self):
        topic_ids = self.get_relations('user_topic_subscribe', 'topic_id')
        topic_ids += self.get_relations('user_topic', 'topic_id')
        topics = Topic.find_all([('topic_id', ' NOT IN', tuple(topic_ids))]) if len(topic_ids) > 0 else []
        return_topics = []
        for i in topics:
            i.__setattr__('type', 'unsubscribed')
            return_topics.append(i)
        return return_topics

    def all_topics(self):
        topics = self.own_topics() + self.subscribe_topics() + self.unsubscribe_topics()
        topics.sort(key=lambda topic: (topic['is_publish'], topic['news_count']), reverse=True)
        return topics

    def add_bookmark(self, link_id):
        self.add_relation('user_bookmark', 'bookmark_link_id', link_id)

    def delete_bookmark(self, link_id):
        self.delete_relation('user_bookmark', 'bookmark_link_id', link_id)

    def bookmarks(self):
        bookmark_ids = self.get_relations('user_bookmark', 'bookmark_link_id')
        return bookmark_ids if len(bookmark_ids) > 0 else [-1]

