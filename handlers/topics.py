"""
Topic Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape

from logic.helper import get_relevant_locations, source_selection
from logic.topics import delete_topic, stop_topic, start_topic, publish_topic, unpublish_topic, subsribe_topic, \
    unsubsribe_topic, get_topic_list, topic_exist, get_topic, update_topic, add_topic
from logic.users import save_topic_id, get_current_topic, get_current_location, set_current_topic, get_topic_limit

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13


class TopicHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        save_topic_id(self.get_argument("topic_id"), user_id)


class TopicsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = get_relevant_locations()
        variables = {
            'title': "Topics",
            'alerts': get_topic_list(user_id),
            'type': "alertlist",
            'alertlimit': get_topic_limit(user_id),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, topic_id=None):
        topic_id = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            delete_topic(topic_id, user_id)
        elif posttype == u'stop':
            stop_topic(topic_id)
        elif posttype == u'start':
            start_topic(topic_id)
        elif posttype == u'publish':
            publish_topic(topic_id)
        elif posttype == u'unpublish':
            unpublish_topic(topic_id)
        elif posttype == u'subscribe':
            subsribe_topic(topic_id, user_id)
            set_current_topic(user_id)
        elif posttype == u'unsubscribe':
            unsubsribe_topic(topic_id, user_id)
            set_current_topic(user_id)
        template = "alerts.html"
        variables = {
            'title': "Topics",
            'alerts': get_topic_list(user_id),
            'type': "alertlist",
            'alertlimit': get_topic_limit(user_id),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        }
        content = self.render_template(template, variables)
        dropdown = self.render_template("alertDropdownMenu.html", variables)
        self.write({'topic_list': content, 'dropdown_list': dropdown})


class CreateEditTopicHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = dict()
        variables['topic'] = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        variables['username'] = str(tornado.escape.xhtml_escape(self.get_current_username()))
        variables['alerts'] = get_topic_list(user_id)
        relevant_locations = get_relevant_locations()
        variables['relevant_locations'] = relevant_locations
        variables['location'] = get_current_location(tornado.escape.xhtml_escape(self.current_user))

        if alertid is not None:
            if topic_exist(user_id):
                variables['title'] = "Edit Topic"
                variables['alert'] = get_topic(alertid)
                variables['type'] = "editAlert"
            else:
                self.redirect("/Topics")
        else:
            if get_topic_limit(user_id) == 0:
                self.redirect("/Topics")
            variables['title'] = "Create Topic"
            variables['alert'] = get_topic(alertid)
            variables['type'] = "createAlert"
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        alert = {}
        alert['keywords'] = ",".join(self.get_argument("keywords").split(","))
        try:
            alert['domains'] = ",".join(self.get_argument("domains").split(","))
        except:
            alert['domains'] = ""
        alert['description'] = self.get_argument("description")
        keywordlimit = 20 - len(self.get_argument("keywords").split(","))
        alert['keywordlimit'] = keywordlimit
        # alert['excludedkeywords'] = ",".join(self.get_argument("excludedkeywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = b','.join(self.request.arguments.get("languages")).decode("utf-8")
        else:
            alert['lang'] = ""

        alert['image'] = self.get_argument("alertimage", '')

        if alertid is not None:
            alert['alertid'] = alertid
            update_topic(alert)
        else:
            alert['name'] = self.get_argument('alertname')
            add_topic(alert, user_id)
        self.redirect("/Topics")


class PagesHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'pages.html'
        keywords_list = self.get_argument("keywords").split(",")

        if keywords_list != ['']:
            sourceSelection = source_selection(keywords_list)
        else:
            sourceSelection = {'pages': [], 'subreddits': []}

        variables = {
            'facebookpages': sourceSelection['pages'],
            'redditsubreddits': sourceSelection['subreddits']
        }

        content = self.render_template(template, variables)
        self.write(content)


class ThemesHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themes = apiv1.getThemes()
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class ThemesV11Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themes = apiv11.getThemes(4)
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class TopicsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        keywords = self.get_argument('keywords', "").split(",")
        topics = apiv12.getTopics(keywords)
        self.set_header('Content-Type', 'application/json')
        self.write(topics)
