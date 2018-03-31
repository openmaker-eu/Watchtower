"""
Documentation Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

from decouple import config

from handlers.base import BaseHandler, TemplateRendering


class DocumentationHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'api.html'
        variables = {
            'title': "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)


class Documentationv11Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv11.html'
        variables = {
            'title': "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)


class Documentationv12Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv12.html'
        variables = {
            'title': "Watchtower Api v1.2"
        }
        content = self.render_template(template, variables)
        self.write(content)


class Documentationv13Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv13.html'
        variables = {
            'title': "Watchtower Api v1.3",
            'host': config("HOST_NAME")
        }
        content = self.render_template(template, variables)
        self.write(content)
