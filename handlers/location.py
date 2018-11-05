"""
Audience Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from logic.users import save_location

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler


class LocationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        save_location(self.get_argument("location"), user_id)