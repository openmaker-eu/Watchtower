"""
User Location Handlers for Watchtower
"""

__author__ = ['Barış Can Esmer', 'Enis Simsar']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv13


class PredictedLocationV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        try:
            user_ids = [int(x) for x in self.get_argument("user_ids",default="",strip=True).split(",")]
        except:
            user_ids = []
        
        locations = apiv13.getPredictedLocations(user_ids)
        self.set_header('Content-Type', 'application/json')
        self.write(locations)
