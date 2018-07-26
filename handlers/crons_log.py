"""
Cron Logs Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.escape
import tornado.web

from logic.crons import get_crons_log
from logic.helper import get_relevant_locations
from logic.topics import get_topic_list
from logic.users import get_current_topic, get_current_location

from handlers.base import BaseHandler, TemplateRendering


class CronsLogHandler(BaseHandler, TemplateRendering):
    def data_received(self, chunk):
        pass

    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = get_relevant_locations()
        crons_log = get_crons_log()

        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Crons Logs",
            'alerts': get_topic_list(user_id),
            'type': "crons_log",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations,
            'crons': crons_log
        }
        content = self.render_template(template, variables)
        self.write(content)
