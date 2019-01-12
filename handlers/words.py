"""
Audience Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from logic.helper import get_relevant_locations
from logic.words import get_words_aggregations
from logic.topics import get_topic_list
from logic.users import get_current_location, get_current_topic

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler


class WordsChartHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        data = get_words_aggregations(topic['topic_id'])
        variables = {
            'title': "Words Charts",
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
            'alertid': topic['topic_id'],
            'alerts': get_topic_list(user_id),
            'alertname': topic['topic_name'],
            'type': "word_chart",
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
        template = 'words.html'
        topic_id = self.get_argument('topic_id', '')
        if topic_id == '':
            topic_id = topic['topic_id']
        topic_id = int(topic_id)
        data = get_words_aggregations(topic_id)
        variables = {
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
        }
        content = self.render_template(template, variables)
        self.write(content)
