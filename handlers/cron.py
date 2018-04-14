"""
Cron Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.escape
import tornado.web

import logic
from handlers.base import BaseHandler, TemplateRendering


class CronHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        crons = logic.get_crons()

        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Crons",
            'alerts': logic.get_topic_list(user_id),
            'type': "crons",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations,
            'crons': crons
        }
        content = self.render_template(template, variables)
        self.write(content)
