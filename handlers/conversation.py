"""
Conversation Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape
import json

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13
import logic
from crontab_module.crons import facebook_reddit_crontab


class PreviewConversationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        keywords_list = self.get_argument("keywords").split(",")
        sources = logic.source_selection(keywords_list)

        reddit_sources = sources['subreddits']
        '''
        facebookSources = sources['pages']
        facebookSourceIds = []
        for source in facebookSources:
            facebookSourceIds.append(source['page_id'])

        facebookDocument = facebook_reddit_crontab.mineFacebookConversations(facebookSourceIds,True,"day")

        print("facebookDocument is: ", facebookDocument)
        redditDocument = facebook_reddit_crontab.mineRedditConversation(redditSources,True,"day")

        docs = facebookDocument + redditDocument
        '''
        docs = facebook_reddit_crontab.mineRedditConversation(reddit_sources, True, "day")
        self.write(self.render_template("submission.html", {"docs": docs}))


class ConversationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        topic_id = self.get_argument("topic_id")
        time_filter = self.get_argument("timeFilter")
        paging = self.get_argument("paging")
        docs = apiv12.getConversations(topic_id, time_filter, paging)
        if docs is None:
            docs = []
        self.write(self.render_template("submission.html", {"docs": docs}))


class ConversationPageHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Conversations",
            'alerts': logic.get_topic_list(user_id),
            'type': "conversation",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            "docs": apiv12.getConversations(topic['topic_id'], "day", 0),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)


class ConversationV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        if topic_id is None:
            self.write({})
        time_filter = self.get_argument("date", "day")
        paging = self.get_argument("cursor", "0")
        docs = apiv12.getConversations(int(topic_id), time_filter, paging)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps({'conversations': docs}))
