"""
Audience Handlers for Watchtower
"""
__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

import tornado.web
import tornado.escape
import pprint

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13
import logic


class AudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(user_id)
        print(" (GET) Getting audience for topic " + str(topic['topic_id']))
        try:
            location = self.get_argument('location')
        except:
            location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")
        audiences = logic.get_audience(topic['topic_id'], user_id, 0, location)
        audience_stats = logic.get_audience_stats(topic['topic_id'], location)
        variables = {
            'title': "Audience",
            'topic': topic,
            'audiences': audiences['audiences'],
            'cursor': audiences['next_cursor'],
            'alerts': logic.get_topic_list(user_id),
            'type': "audiences",
            'audience_stats': audience_stats,
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'location': location,
            'relevant_locations': relevant_locations
        }

        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        variables = {}
        user_id = tornado.escape.xhtml_escape(self.current_user)
        topic = logic.get_current_topic(user_id)
        topic_id = topic['topic_id']
        print(" (POST) Getting audience for topic " + str(topic_id))
        try:
            location = self.get_argument('location')
            print("got location from JS.")
        except:
            location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))

        if argument is not None:  # scroll
            print("Scrolled down.")
            template = 'audienceTemplate.html'
            try:
                next_cursor = self.get_argument('next_cursor')
            except:
                next_cursor = 0
                pass
            try:
                audiences = logic.get_audience(topic_id, user_id, int(next_cursor), location)
                audience_stats = logic.get_audience_stats(topic_id, location)

                variables = {
                    'audiences': audiences['audiences'],
                    'audience_stats': audience_stats,
                    'cursor': audiences['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        else:  # change in topic or location dropdown
            try:
                topic_id = self.get_argument('topic_id')
                print("Changed topic.")
            except:
                print("Changed location.")
            template = 'alertAudience.html'
            user_id = tornado.escape.xhtml_escape(self.current_user)
            try:
                audiences = logic.get_audience(topic_id, user_id, 0, location)
                audience_stats = logic.get_audience_stats(topic_id, location)

                variables = {
                    'audiences': audiences['audiences'],
                    'audience_stats': audience_stats,
                    'topic_id': topic_id,
                    'cursor': audiences['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        content = self.render_template(template, variables)
        self.write(content)


class RateAudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        audience_id = self.get_argument("audience_id")
        topic_id = self.get_argument("topic_id")
        rating = self.get_argument("rating")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.rate_audience(topic_id, user_id, audience_id, rating)
        self.write("")


class AudienceV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        audiences = apiv12.getAudiences(topic_id)
        self.set_header('Content-Type', 'application/json')
        self.write(audiences)


class AudienceSampleV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = str(self.get_argument("topic_id", None))
        location = str(self.get_argument("location", ""))
        try:
            cursor = int(self.get_argument('cursor', '0'))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        audience_sample = apiv13.getAudienceSample(topic_id, location, int(cursor))
        self.set_header('Content-Type', 'application/json')
        self.write(audience_sample)
