import json
import os
import random
import string

import tornado.ioloop
import tornado.options
import tornado.web
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from raven.contrib.tornado import AsyncSentryClient, SentryMixin

# API VERSIONS
from apis import apiv12, apiv13, apiv1, apiv11

from crontab_module.crons import facebook_reddit_crontab
import logic

from decouple import config


chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace(
    '\\', '')
secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(100)])
secret_key = 'PEO+{+RlTK[3~}TS-F%[9J/sIp>W7!r*]YV75GZV)e;Q8lAdNE{m@oWK.+u-&z*-p>~Xa!Z8j~{z,BVv.e0GChY{(1.KVForO#rQ'

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=False,
    cookie_secret=secret_key,
    login_url="/login",
)


class TemplateRendering:
    def render_template(self, template_name, variables={}):
        env = Environment(loader=FileSystemLoader(settings['template_path']))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        content = template.render(variables)
        return content


class BaseHandler(SentryMixin, tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

    def get_current_username(self):
        return self.get_secure_cookie("username")


class Api500ErrorHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.write(json.dumps({'error': "Unexpected Error!"}))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/logout", LogoutHandler),
            (r"/login", LoginHandler),
            (r"/register", RegisterHandler),
            (r"/profile", ProfileHandler),
            (r"/Topics", TopicsHandler),
            (r"/topicinfo", CreateEditTopicHandler),
            (r"/topicinfo/([0-9]*)", CreateEditTopicHandler),
            (r"/Feed/(.*)", FeedHandler),
            (r"/Feed", FeedHandler),
            (r"/Conversations/(.*)", ConversationPageHandler),
            (r"/Conversations", ConversationPageHandler),
            (r"/Comments/(.*)", ConversationHandler),
            (r"/Comments", ConversationHandler),
            (r"/Events/(.*)", EventPageHandler),
            (r"/Events", EventPageHandler),
            (r"/get_events/(.*)", EventHandler),
            (r"/get_events", EventHandler),
            (r"/News/(.*)", NewsHandler),
            (r"/News", NewsHandler),
            (r"/Search", SearchHandler),
            (r"/get_news", SearchNewsHandler),
            (r"/get_news/(.*)", SearchNewsHandler),
            (r"/Audience/(.*)", AudienceHandler),
            (r"/Audience", AudienceHandler),

            (r"/Influencers/(.*)", LocalInfluencersHandler), # added for influencers
            (r"/Influencers", LocalInfluencersHandler),
            (r"/hide_influencer", HideInfluencerHandler),

            (r"/Tweets/(.*)", TweetsHandler),
            (r"/Tweets", TweetsHandler),

            (r"/Recommendations/(.*)", RecommendationsHandler), # added for recommendations
            (r"/Recommendations", RecommendationsHandler),

            (r"/previewNews", PreviewNewsHandler),
            (r"/previewConversations", PreviewConversationHandler),
            (r"/previewEvents", PreviewEventHandler),
            (r"/rate_audience", RateAudienceHandler),
            (r"/sentiment", SentimentHandler),
            (r"/bookmark", BookmarkHandler),
            (r"/domain", DomainHandler),
            (r"/newTweets", NewTweetsHandler),
            (r"/newTweets/(.*)", NewTweetsHandler),
            (r"/saveTopicId", TopicHandler),
            (r"/saveLocation", LocationHandler),
            (r"/getPages", PagesHandler),

            # DOCUMENTATIONS
            (r"/api", DocumentationHandler),
            (r"/api/v1\.1", Documentationv11Handler),
            (r"/api/v1\.2", Documentationv12Handler),
            (r"/api/v1\.3", Documentationv13Handler),

            # API V1
            (r"/api/get_themes", ThemesHandler),
            (r"/api/get_influencers/(.*)/(.*)", InfluencersHandler),
            (r"/api/get_feeds/(.*)/(.*)", FeedsHandler),
            (r"/api/get_influencers/(.*)", InfluencersHandler),
            (r"/api/get_feeds/(.*)", FeedsHandler),

            # API V1.1
            (r"/api/v1.1/get_themes", ThemesV11Handler),
            (r"/api/v1.1/get_feeds", FeedsV11Handler),
            (r"/api/v1.1/get_influencers", InfluencersV11Handler),

            # API V1.2
            (r"/api/v1.2/get_topics", TopicsV12Handler),
            (r"/api/v1.2/get_news", NewsFeedsV12Handler),
            (r"/api/v1.2/get_audiences", AudiencesV12Handler),
            (r"/api/v1.2/search_news", NewsV12Handler),
            (r"/api/v1.2/get_events", EventV12Handler),
            (r"/api/v1.2/get_conversations", ConversationV12Handler),
            (r"/api/v1.2/get_hashtags", HashtagsV12Handler),

            # API V1.3
            # get_audiences deprecated
            (r"/api/v1.3/get_topics", TopicsV12Handler),
            (r"/api/v1.3/get_audience_sample", AudienceSampleV13Handler), # new
            (r"/api/v1.3/get_local_influencers", LocalInfluencersV13Handler), # new
            (r"/api/v1.3/get_news", NewsFeedsV13Handler), # changed
            (r"/api/v1.3/search_news", NewsV13Handler), # changed
            (r"/api/v1.3/get_events", EventV13Handler), # changed
            (r"/api/v1.3/get_conversations", ConversationV12Handler),
            (r"/api/v1.3/get_hashtags", HashtagsV12Handler),

            (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)

class NewsFeedsV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        forbidden_domain = self.get_argument("forbidden_domains", "").split(",")
        topics = self.get_argument('topic_ids', "").split(",")
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        date = str(self.get_argument("date", "month"))
        news = apiv13.getNewsFeeds(date, cursor, forbidden_domain, topics)
        self.set_header('Content-Type', 'application/json')
        self.write(news)

class NewsV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        news_ids = self.get_argument('news_ids', "").split(",")
        keywords = self.get_argument('keywords', "").split(",")
        languages = self.get_argument('languages', "").split(",")
        countries = self.get_argument('countries', "").split(",")
        cities = self.get_argument('cities', "").split(",")
        user_location = self.get_argument('mention_location', "").split(",")
        user_language = self.get_argument('mention_language', "").split(",")
        since = self.get_argument('since', "")
        until = self.get_argument('until', "")
        topics = self.get_argument('topic_ids', "").split(",")
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        news = apiv13.getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor,
                              since, until, [""], topics)
        self.set_header('Content-Type', 'application/json')
        self.write(news)


class EventV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = str(self.get_argument("topic_id", None))
        if topic_id is None:
            self.write({})
        sortedBy = str(self.get_argument('sortedBy', ""))
        location = str(self.get_argument("location",""))
        try:
            cursor = int(self.get_argument('cursor', '0'))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        events = apiv13.getEvents(topic_id, sortedBy, location, int(cursor))
        self.set_header('Content-Type', 'application/json')
        self.write(events)

class AudienceSampleV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = str(self.get_argument("topic_id", None))
        location = str(self.get_argument("location",""))
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

class LocalInfluencersV13Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = str(self.get_argument("topic_id", None))
        location = str(self.get_argument("location",""))
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

class Documentationv13Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv13.html'
        variables = {
            'title': "Watchtower Api v1.3",
            'host': config("HOST_NAME")
        }
        content = self.render_template(template, variables)
        self.write(content)

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


class ConversationV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        if topic_id is None:
            self.write({})
        timeFilter = self.get_argument("date", "day")
        paging = self.get_argument("cursor", "0")
        docs = apiv12.getConversations(int(topic_id), timeFilter, paging)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps({'conversations': docs}))


class TopicsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        keywords = self.get_argument('keywords', "").split(",")
        topics = apiv12.getTopics(keywords)
        self.set_header('Content-Type', 'application/json')
        self.write(topics)


class NewsFeedsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        forbidden_domain = self.get_argument("forbidden_domains", "").split(",")
        topics = self.get_argument('topic_ids', "").split(",")
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        date = str(self.get_argument("date", "month"))
        news = apiv12.getNewsFeeds(date, cursor, forbidden_domain, topics)
        self.set_header('Content-Type', 'application/json')
        self.write(news)


class AudiencesV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        audiences = apiv12.getAudiences(topic_id)
        self.set_header('Content-Type', 'application/json')
        self.write(audiences)


class HashtagsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        date = self.get_argument("date", "yesterday")
        hashtags = apiv12.getHastags(topic_id, date)
        self.set_header('Content-Type', 'application/json')
        self.write(hashtags)


class NewsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        news_ids = self.get_argument('news_ids', "").split(",")
        keywords = self.get_argument('keywords', "").split(",")
        languages = self.get_argument('languages', "").split(",")
        countries = self.get_argument('countries', "").split(",")
        cities = self.get_argument('cities', "").split(",")
        user_location = self.get_argument('mention_location', "").split(",")
        user_language = self.get_argument('mention_language', "").split(",")
        since = self.get_argument('since', "")
        until = self.get_argument('until', "")
        topics = self.get_argument('topic_ids', "").split(",")
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        news = apiv12.getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor,
                              since, until, [""], topics)
        self.set_header('Content-Type', 'application/json')
        self.write(news)


class Documentationv12Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv12.html'
        variables = {
            'title': "Watchtower Api v1.2"
        }
        content = self.render_template(template, variables)
        self.write(content)


class ThemesV11Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themes = apiv11.getThemes(4)
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class FeedsV11Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        date = str(self.get_argument("date", "month"))
        feeds = apiv11.getFeeds(themename, themeid, 4, date, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)


class InfluencersV11Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        influencers = apiv11.getInfluencers(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)


class Documentationv11Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv11.html'
        variables = {
            'title': "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)


class ThemesHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        themes = apiv1.getThemes()
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class InfluencersHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self, themename, cursor=None):
        influencers = apiv1.getInfluencers(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)


class FeedsHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self, themename, cursor=None):
        feeds = apiv1.getFeeds(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)


class DocumentationHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'api.html'
        variables = {
            'title': "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)


class MainHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'index.html'
        variables = {
            'title': "Watchtower"
        }
        content = self.render_template(template, variables)
        self.write(content)


class RegisterHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'register.html'
        variables = {
            'title': "Register Page"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self):
        username = self.get_argument("username")
        password = str(self.get_argument("password"))
        country = str(self.get_argument("country"))
        register_info = logic.register(str(username), password, country.upper())
        if register_info['response']:
            self.set_secure_cookie("user_id", str(register_info['user_id']))
            self.set_secure_cookie("username", str(username))
            self.write({'response': True, 'redirectUrl': '/Topics'})
        else:
            self.write(json.dumps(register_info))


class LoginHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'login.html'
        variables = {
            'title': "Login Page"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self):
        username = self.get_argument("username")
        login_info = logic.login(str(username), str(self.get_argument("password")))
        if login_info['response']:
            self.set_secure_cookie("user_id", str(login_info['user_id']))
            self.set_secure_cookie("username", str(username))
            logic.set_current_topic(str(login_info['user_id']))
            self.write({'response': True, 'redirectUrl': self.get_argument('next', '/Topics')})
        else:
            self.write(json.dumps(login_info))


class LogoutHandler(BaseHandler, TemplateRendering):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")


class ProfileHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        user = logic.get_user(user_id)
        auth_url = logic.get_twitter_auth_url()
        variables = {
            'title': "My Profile",
            'type': "profile",
            'username': user['username'],
            'country': user['country'],
            'alerts': logic.get_topic_list(user_id),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations,
            'auth_url': auth_url[0]
        }
        self.set_secure_cookie("request_token", str(auth_url[1]))
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        password = str(self.get_argument("password"))
        country = str(self.get_argument("country"))
        twitter_pin = self.get_argument("twitter_pin", "")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        auth_token = self.get_secure_cookie("request_token")
        self.clear_cookie("request_token")
        update_info = logic.update_user(user_id, password, country.upper(), auth_token, twitter_pin)
        if update_info['response']:
            self.write({'response': True, 'redirectUrl': '/Topics'})
        else:
            self.write(json.dumps(update_info))


class TopicsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        variables = {
            'title': "Topics",
            'alerts': logic.get_topic_list(user_id),
            'type': "alertlist",
            'alertlimit': logic.get_topic_limit(user_id),
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
            logic.delete_topic(topic_id, user_id)
        elif posttype == u'stop':
            logic.stop_topic(topic_id)
        elif posttype == u'start':
            logic.start_topic(topic_id)
        elif posttype == u'publish':
            logic.publish_topic(topic_id)
        elif posttype == u'unpublish':
            logic.unpublish_topic(topic_id)
        elif posttype == u'subscribe':
            logic.subsribe_topic(topic_id, user_id)
            logic.set_current_topic(user_id)
        elif posttype == u'unsubscribe':
            logic.unsubsribe_topic(topic_id, user_id)
            logic.set_current_topic(user_id)
        template = "alerts.html"
        variables = {
            'title': "Topics",
            'alerts': logic.get_topic_list(user_id),
            'type': "alertlist",
            'alertlimit': logic.get_topic_limit(user_id),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        }
        content = self.render_template(template, variables)
        dropdown = self.render_template("alertDropdownMenu.html", variables)
        self.write({'topic_list': content, 'dropdown_list': dropdown})


class CreateEditTopicHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {}
        variables['topic'] = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        variables['username'] = str(tornado.escape.xhtml_escape(self.get_current_username()))
        variables['alerts'] = logic.get_topic_list(user_id)
        relevant_locations = logic.get_relevant_locations()
        variables['relevant_locations'] = relevant_locations
        variables['location'] = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))

        if alertid != None:
            if logic.topic_exist(user_id):
                variables['title'] = "Edit Topic"
                variables['alert'] = logic.get_topic(alertid)
                variables['type'] = "editAlert"
            else:
                self.redirect("/Topics")
        else:
            if logic.get_topic_limit(user_id) == 0:
                self.redirect("/Topics")
            variables['title'] = "Create Topic"
            variables['alert'] = logic.get_topic(alertid)
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
        keywordlimit = 10 - len(self.get_argument("keywords").split(","))
        alert['keywordlimit'] = keywordlimit
        # alert['excludedkeywords'] = ",".join(self.get_argument("excludedkeywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = b','.join(self.request.arguments.get("languages")).decode("utf-8")
        else:
            alert['lang'] = ""

        if alertid != None:
            alert['alertid'] = alertid
            logic.update_topic(alert)
        else:
            alert['name'] = self.get_argument('alertname')
            logic.add_topic(alert, user_id)
        self.redirect("/Topics")


class PreviewNewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'newsTemplate.html'
        keywords = self.get_argument("keywords")
        # exculdedkeywords = self.get_argument("excludedkeywords")
        languages = self.get_argument("languages")
        variables = {
            'feeds': logic.search_news(keywords, languages)
        }

        print(variables['feeds'])

        if len(variables['feeds']) == 0:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)


class BookmarkHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        variables = {
            'title': "Bookmark",
            'feeds': logic.get_bookmarks(user_id),
            'alertid': topic['topic_id'],
            'alerts': logic.get_topic_list(user_id),
            'alertname': topic['topic_name'],
            'type': "bookmark",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alert_id = self.get_argument("alertid")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        posttype = self.get_argument("posttype")
        if posttype == "add":
            logic.add_bookmark(user_id, link_id)
        else:
            logic.remove_bookmark(user_id, link_id)
        self.write("")

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

class RateAudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        audience_id = self.get_argument("audience_id")
        alertid = self.get_argument("alertid")
        rating = self.get_argument("rating")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.rate_audience(alertid, user_id, audience_id, rating)
        self.write("")


class SentimentHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alertid = self.get_argument("alertid")
        rating = self.get_argument("rating")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.sentiment_news(alertid, user_id, link_id, rating)
        self.write("")


class DomainHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        domain = self.get_argument("domain")
        alertid = self.get_argument("alertid")
        logic.ban_domain(user_id, alertid, domain)
        self.write({})


# This handler gets all tweets about given topic
class FeedHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'

        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        tweets = logic.get_tweets(topic['topic_id'])
        variables = {
            'title': "Feed",
            'alerts': logic.get_topic_list(user_id),
            'type': "feed",
            'tweets': tweets,
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user)),
            'location': location,
            'relevant_locations': relevant_locations
        }

        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        if argument is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            lastTweetId = self.get_argument('lastTweetId')
            variables = {
                'tweets': logic.get_skip_tweets(alertid, lastTweetId)
            }
        else:
            template = 'alertFeed.html'
            alertid = self.get_argument('alertid')
            variables = {
                'tweets': logic.get_tweets(alertid),
                'alertid': alertid
            }
            if len(variables['tweets']) == 0:
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)


class NewTweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self, get=None):
        if get is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            variables = {
                'tweets': logic.get_new_tweets(alertid, newestId)
            }
            content = self.render_template(template, variables)
        else:
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            content = str(logic.check_tweets(alertid, newestId))
        self.write(content)


class NewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        feeds = logic.get_news(user_id, topic['topic_id'], "yesterday", 0)
        variables = {
            'title': "News",
            'feeds': feeds['feeds'],
            'cursor': feeds['next_cursor'],
            'alertid': topic['topic_id'],
            'alerts': logic.get_topic_list(user_id),
            'alertname': topic['topic_name'],
            'type': "news",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        variables = {}
        if argument is not None:
            template = 'newsTemplate.html'
            alertid = self.get_argument('alertid')
            try:
                next_cursor = self.get_argument('next_cursor')
            except:
                next_cursor = 0
                pass
            try:
                date = self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            try:
                feeds = logic.get_news(user_id, alertid, date, int(next_cursor))
                variables = {
                    'feeds': feeds['feeds'],
                    'cursor': feeds['next_cursor'],
                }
            except Exception as e:
                print(e)
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        else:
            template = 'alertNews.html'
            alertid = self.get_argument('alertid')
            try:
                date = self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            try:
                feeds = logic.get_news(user_id, alertid, date, 0)
                variables = {
                    'feeds': feeds['feeds'],
                    'cursor': feeds['next_cursor'],
                    'alertid': alertid
                }
            except Exception as e:
                print(e)
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)


class SearchHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        variables = {}
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title': "Search",
            'type': "search",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': None
        }

        content = self.render_template(template, variables)
        self.write(content)


class SearchNewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        keywords = self.get_argument('keywords').split(",")
        domains = self.get_argument('domains').split(",")
        languages = self.get_argument('languages').split(",")
        countries = self.get_argument('countries').split(",")
        cities = self.get_argument('cities').split(",")
        user_location = self.get_argument("mention_location").split(",")
        user_language = self.get_argument('mention_language').split(",")
        since = ""
        until = ""

        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass

        if argument is not None:
            template = 'newsTemplate.html'
        else:
            template = "alertNews.html"

        news = apiv12.getNews([""], keywords, languages, cities, countries, user_location, user_language, cursor, since,
                              until, domains)
        news = json.loads(news)
        if news['news'] == []:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        variables = {
            'feeds': news['news'],
            'cursor': news['next_cursor_str']
        }

        content = self.render_template(template, variables)
        self.write(content)

class LocalInfluencersHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
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
            'recom_filter':'recommended',
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
                audience = logic.get_recommended_audience(topic['topic_id'], location, filter, user_id, int(next_cursor))
                variables = {
                    'audience': audience['audience'],
                    'cursor': audience['next_cursor'],
                    'recom_filter':filter
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
                    'recom_filter':filter
                }
            except Exception as e:
                print(e)
                self.write("")
        content = self.render_template(template, variables)
        self.write(content)

class AudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        relevant_locations = logic.get_relevant_locations()
        if topic is None:
            self.redirect("/topicinfo")

        audiences = logic.get_audience(topic['topic_id'], user_id, 0, location)
        variables = {
            'title': "Audience",
            'alertname': topic['topic_name'],
            'alertid': topic['topic_id'],
            'audiences': audiences['audiences'],
            'cursor': audiences['next_cursor'],
            'alerts': logic.get_topic_list(user_id),
            'type': "audiences",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations
        }

        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        variables = {}
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        user_id = tornado.escape.xhtml_escape(self.current_user)
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        if argument is not None:
            template = 'audienceTemplate.html'
            alertid = self.get_argument('alertid')
            try:
                next_cursor = self.get_argument('next_cursor')
            except:
                next_cursor = 0
                pass
            try:
                audiences = logic.get_audience(topic['topic_id'], user_id, int(next_cursor), location)
                variables = {
                    'audiences': audiences['audiences'],
                    'cursor': audiences['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        else:
            template = 'alertAudience.html'
            alertid = self.get_argument('alertid')
            user_id = tornado.escape.xhtml_escape(self.current_user)
            try:
                audiences = logic.get_audience(alertid, user_id, 0, location)
                variables = {
                    'audiences': audiences['audiences'],
                    'alertid': alertid,
                    'cursor': audiences['next_cursor']
                }
            except Exception as e:
                print(e)
                self.write("")
        content = self.render_template(template, variables)
        self.write(content)

class TweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, tweet_id=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        changing_topic = int(self.get_argument("topic_id", -1))
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = logic.get_current_location(tornado.escape.xhtml_escape(self.current_user))
        if changing_topic != -1:
            topic['topic_id'] = changing_topic
            template = 'renderTweets.html'
        relevant_locations = logic.get_relevant_locations()
        new_tweet = False
        if tweet_id is not None:
            news_id = int(self.get_argument("news_id", -1))
            date = self.get_argument("date", "")
            new_tweet = int(tweet_id) == -1
            tweets = logic.get_publish_tweet(topic['topic_id'], user_id, tweet_id, news_id, date)
        else:
            tweets = logic.get_publish_tweets(topic['topic_id'], user_id)

        variables = {
            'title': "Tweets",
            'alerts': logic.get_topic_list(user_id),
            'type': "tweets",
            'new_tweet': new_tweet,
            'alertlimit': logic.get_topic_limit(user_id),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations,
            'tweets': tweets
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, tweet_id=None):
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        tweet_id = self.get_argument("tweet_id")
        posttype = self.get_argument("posttype")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            logic.delete_publish_tweet(topic['topic_id'], user_id, tweet_id)
        elif posttype == u'update':
            news_id = self.get_argument("news_id")
            date = self.get_argument("date")
            text = self.get_argument("text")
            logic.update_publish_tweet(topic['topic_id'], user_id, tweet_id, date, text, news_id)
        if tweet_id is not None:
            self.redirect("/Tweets")
        else:
            self.write({'response': True})


class PagesHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'pages.html'
        keywordsList = self.get_argument("keywords").split(",")

        if keywordsList != ['']:
            sourceSelection = logic.source_selection(keywordsList)
        else:
            sourceSelection = {'pages': [], 'subreddits': []}

        variables = {
            'facebookpages': sourceSelection['pages'],
            'redditsubreddits': sourceSelection['subreddits']
        }

        content = self.render_template(template, variables)
        self.write(content)


class TopicHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.save_topic_id(self.get_argument("topic_id"), user_id)


class LocationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.save_location(self.get_argument("location"), user_id)


class PreviewEventHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        keywords = self.get_argument('keywords', '0')
        keywordsList = self.get_argument("keywords").split(",")
        sources = facebook_reddit_crontab.sourceSelection(keywordsList)
        t = []
        for source in sources:
            ids = []
            for event in source['events']:
                ids.append(event['event_id'])
            t.extend(facebook_reddit_crontab.mineEvents(ids, True))
            if len(t) > 4:
                break
        temp = []
        for a, b in t:
            temp.append(a)

        document = {"events": temp}
        self.write(self.render_template("single-event.html", {"document": document}))


class PreviewConversationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        keywords = self.get_argument('keywords', '0')
        keywordsList = self.get_argument("keywords").split(",")
        sources = logic.source_selection(keywordsList)

        redditSources = sources['subreddits']
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
        docs = facebook_reddit_crontab.mineRedditConversation(redditSources, True, "day")
        self.write(self.render_template("submission.html", {"docs": docs}))


class EventPageHandler(BaseHandler, TemplateRendering):
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
            'title': "Events",
            'alerts': logic.get_topic_list(user_id),
            'type': "events",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            "document": apiv12.getEvents(topic['topic_id'], "date", 0),
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
        cursor = self.get_argument('cursor')
        document = apiv12.getEvents(topic_id, filter, cursor)
        self.write(self.render_template("single-event.html", {"document": document}))


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


class ConversationHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        topic_id = self.get_argument("topic_id")
        timeFilter = self.get_argument("timeFilter")
        paging = self.get_argument("paging")
        docs = apiv12.getConversations(topic_id, timeFilter, paging)
        if docs == None:
            docs = []
        self.write(self.render_template("submission.html", {"docs": docs}))


def main():
    tornado.options.parse_command_line()
    app = Application()
    try:
        app.sentry_client = AsyncSentryClient(config("SENTRY_TOKEN"))
    except:
        pass
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
