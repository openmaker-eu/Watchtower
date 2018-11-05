"""
Audience Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from logic.hashtags import topic_hashtag, get_hashtag_aggregations
from logic.helper import get_relevant_locations
from logic.topics import get_topic_list
from logic.users import get_current_topic, get_current_location

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler


class HashtagHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        topic_id = self.get_argument('topic_id')
        hashtag = self.get_argument('hashtag')
        save_type = self.get_argument('save_type')
        save_type = True if save_type == 'true' else False
        topic_hashtag(topic_id, hashtag, save_type)


class HashtagChartHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        data = get_hashtag_aggregations(topic['topic_id'])
        variables = {
            'title': "Hashtag Charts",
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
            'alertid': topic['topic_id'],
            'alerts': get_topic_list(user_id),
            'alertname': topic['topic_name'],
            'type': "hashtag_chart",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        template = 'hashtags.html'
        topic_id = self.get_argument('topic_id', '')
        if topic_id == '':
            topic_id = topic['topic_id']
        topic_id = int(topic_id)
        data = get_hashtag_aggregations(topic_id)
        variables = {
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
        }
        content = self.render_template(template, variables)
        self.write(content)
