"""
Recommendation Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
import logic


class RecommendationsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()

        if topic is None:
            self.redirect("/topicinfo")

        audience = logic.get_recommended_audience(topic['topic_id'], location, 'recommended', user_id, 0)
        variables = {
            'title': "Recommendations",
            'alertname': topic['topic_name'],
            'alertid': topic['topic_id'],
            'location': location,
            'audience': audience['audience'],
            'cursor': audience['next_cursor'],
            'alerts': logic.get_topic_list(user_id),
            'recom_filter': 'recommended',
            'type': "recommendations",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'relevant_locations': relevant_locations
        }

        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        variables = {}
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        user_id = tornado.escape.xhtml_escape(self.current_user)
        filter = self.get_argument('filter')

        if argument is not None:
            template = 'recommendationsTemplate.html'
            try:
                next_cursor = self.get_argument('next_cursor')
            except:
                next_cursor = 0
                pass
            try:
                # filter is "rated" or "recommended"
                audience = logic.get_recommended_audience(topic['topic_id'], location, filter, user_id,
                                                          int(next_cursor))
                variables = {
                    'audience': audience['audience'],
                    'cursor': audience['next_cursor'],
                    'recom_filter': filter
                }
            except Exception as e:
                print(e)
                self.write("")
        else:
            template = 'alertRecommendations.html'
            try:
                audience = logic.get_recommended_audience(topic['topic_id'], location, filter, user_id, 0)
                variables = {
                    'audience': audience['audience'],
                    'alertid': topic['topic_id'],
                    'cursor': audience['next_cursor'],
                    'recom_filter': filter
                }
            except Exception as e:
                print(e)
                self.write("")
        content = self.render_template(template, variables)
        self.write(content)
