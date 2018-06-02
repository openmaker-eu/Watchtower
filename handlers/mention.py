"""
Audience Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
import logic


class MentionChartHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        data = logic.get_mention_aggregations(topic['topic_id'])
        variables = {
            'title': "Mention Charts",
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
            'alertid': topic['topic_id'],
            'alerts': logic.get_topic_list(user_id),
            'alertname': topic['topic_name'],
            'type': "mention_chart",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        template = 'mentions.html'
        topic_id = self.get_argument('topic_id', '')
        if topic_id == '':
            topic_id = topic['topic_id']
        topic_id = int(topic_id)
        data = logic.get_mention_aggregations(topic_id)
        variables = {
            'data': data['data'],
            'sorted': data['sorted'],
            'table_data': data['table_data'],
        }
        content = self.render_template(template, variables)
        self.write(content)
