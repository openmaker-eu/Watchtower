"""
Audience Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
import logic


class LocationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.save_location(self.get_argument("location"), user_id)