"""
Audience Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
import logic


class HashtagHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        topic_id = self.get_argument('topic_id')
        hashtag = self.get_argument('hashtag')
        save_type = self.get_argument('save_type')
        save_type = True if save_type == 'true' else False
        logic.topic_hashtag(topic_id, hashtag, save_type)