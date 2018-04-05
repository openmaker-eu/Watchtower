"""
Influencer Handlers for Watchtower
"""
__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13
import logic


class LocalInfluencersHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        try:
            location = self.get_argument('location')
        except:
            location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()

        if topic is None:
            self.redirect("/topicinfo")

        local_influencers = logic.get_local_influencers(topic['topic_id'], 0, location)
        variables = {
            'title': "Influencers",
            'alertname': topic['topic_name'],
            'alertid': topic['topic_id'],
            'location': location,
            'local_influencers': local_influencers['local_influencers'],
            'cursor': local_influencers['next_cursor'],
            'alerts': logic.get_topic_list(user_id),
            'type': "influencers",
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
        try:
            location = self.get_argument('location')
        except:
            location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        user_id = tornado.escape.xhtml_escape(self.current_user)

        if argument is not None:
            template = 'influencersTemplate.html'
            try:
                next_cursor = self.get_argument('next_cursor')
            except:
                next_cursor = 0
                pass
            try:
                local_influencers = logic.get_local_influencers(topic['topic_id'], int(next_cursor), location)
                variables = {
                    'local_influencers': local_influencers['local_influencers'],
                    'cursor': local_influencers['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        else:
            template = 'alertInfluencers.html'
            try:
                local_influencers = logic.get_local_influencers(topic['topic_id'], 0, location)
                variables = {
                    'local_influencers': local_influencers['local_influencers'],
                    'alertid': topic['topic_id'],
                    'cursor': local_influencers['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        content = self.render_template(template, variables)
        self.write(content)


class HideInfluencerHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        influencer_id = str(self.get_argument("influencer_id"))
        topic_id = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))['topic_id']
        is_hide = (self.get_argument("is_hide") == "true")
        description = self.get_argument("description")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        logic.hide_influencer(topic_id, user_id, influencer_id, description, is_hide, location)
        self.write("")


class FetchFollowersHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        influencer_id = str(self.get_argument("influencer_id"))
        fetching = (self.get_argument("fetching") == "true")
        logic.add_or_delete_fetch_followers_job(user_id, influencer_id, fetching)
        self.write("")


"""
API handlers
"""

class InfluencersHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self, themename, cursor=None):
        influencers = apiv1.getInfluencers(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)


class InfluencersV11Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        influencers = apiv11.getInfluencers(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)


class LocalInfluencersV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
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

        local_influencers = apiv13.getLocalInfluencers(topic_id, location, int(cursor))
        self.set_header('Content-Type', 'application/json')
        self.write(local_influencers)
