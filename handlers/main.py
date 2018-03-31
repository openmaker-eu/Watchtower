"""
Main Handler for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

from handlers.base import BaseHandler, TemplateRendering


class MainHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'index.html'
        variables = {
            'title': "Watchtower"
        }
        content = self.render_template(template, variables)
        self.write(content)

