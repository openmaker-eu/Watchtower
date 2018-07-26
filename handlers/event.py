"""
Event Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape
import json

from logic.events import get_events, hide_event
from logic.helper import get_relevant_locations
from logic.topics import get_topic_list
from logic.users import get_current_topic, get_current_location

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv12, apiv13
from crontab_module.crons.get_events import mineEventsFromEventBrite
from crontab_module.crons.facebook_reddit_crontab import sourceSelection


class PreviewEventHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        keywords_list = self.get_argument("keywords").split(",")
        sources = sourceSelection(keywords_list)
        t = []
        for source in sources:
            ids = []
            for event in source['events']:
                ids.append(event['event_id'])
            t.extend(mineEventsFromEventBrite(ids))
            if len(t) > 4:
                break
        temp = []
        for a, b in t:
            temp.append(a)

        document = {"events": temp}
        self.write(self.render_template("single-event.html", {"document": document}))


class EventPageHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = get_relevant_locations()
        events = get_events(topic['topic_id'], "date", location, 0)

        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Events",
            'alerts': get_topic_list(user_id),
            'type': "events",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'cursor': events['next_cursor'],
            "document": events,
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)


class EventHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        topic_id = self.get_argument('topic_id')
        filter = self.get_argument('filter')
        try:
            cursor = self.get_argument('cursor')
        except:
            cursor = 0
            pass
        try:
            location = self.get_argument('location')  # this will be called upon a change in location
        except:
            location = get_current_location(tornado.escape.xhtml_escape(
                self.current_user))  # this will be called when new events are loading (cursoring)
        print("CURSOR:" + str(cursor))
        document = get_events(topic_id, filter, location, cursor)
        self.write(self.render_template("single-event.html", {"document": document}))


class HideEventHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        event_link = str(self.get_argument("event_link"))
        topic_id = get_current_topic(tornado.escape.xhtml_escape(self.current_user))['topic_id']
        is_hide = (self.get_argument("is_hide") == "true")
        description = self.get_argument("description")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        hide_event(topic_id, user_id, event_link, description, is_hide)
        self.write("")


class EventV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument('topic_id', None)
        if topic_id is None:
            self.write({})
        date = self.get_argument('date', 'date')
        cursor = self.get_argument('cursor', '0')
        document = apiv12.getEvents(topic_id, date, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(document))


class EventV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = str(self.get_argument("topic_id", None))
        if topic_id is None:
            self.write({})
        sorted_by = str(self.get_argument('sortedBy', ""))
        location = str(self.get_argument("location", ""))
        try:
            cursor = int(self.get_argument('cursor', '0'))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        event_ids = self.get_argument("event_ids", None)
        if event_ids is not None:
            event_ids= event_ids.split(",")
        print(event_ids)
        events = apiv13.getEvents(topic_id, sorted_by, location, int(cursor), event_ids)
        self.set_header('Content-Type', 'application/json')
        self.write(events)