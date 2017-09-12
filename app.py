import json
import os
import random
import string
from threading import Thread

import tornado.ioloop
import tornado.options
import tornado.web
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

import apiv12
import facebook_reddit_crontab
import logic
import apiv11
import apiv1

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


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, mainT):
        self.mainT = mainT

    def get_current_user(self):
        return self.get_secure_cookie("userid")

    def get_current_username(self):
        return self.get_secure_cookie("username")


class Application(tornado.web.Application):
    def __init__(self, mainT):
        handlers = [
            (r"/", MainHandler, {'mainT': mainT}),
            (r"/logout", LogoutHandler, {'mainT': mainT}),
            (r"/login", LoginHandler, {'mainT': mainT}),
            (r"/Topics", TopicsHandler, {'mainT': mainT}),
            (r"/topicinfo", CreateEditTopicHandler, {'mainT': mainT}),
            (r"/topicinfo/([0-9]*)", CreateEditTopicHandler, {'mainT': mainT}),
            (r"/Feed/(.*)", FeedHandler, {'mainT': mainT}),
            (r"/Feed", FeedHandler, {'mainT': mainT}),
            (r"/Conversations/(.*)", ConversationPageHandler, {'mainT': mainT}),
            (r"/Conversations", ConversationPageHandler, {'mainT': mainT}),
            (r"/Comments/(.*)", ConversationHandler, {'mainT': mainT}),
            (r"/Comments", ConversationHandler, {'mainT': mainT}),
            (r"/Events/(.*)", EventPageHandler, {'mainT': mainT}),
            (r"/Events", EventPageHandler, {'mainT': mainT}),
            (r"/get_events/(.*)", EventHandler, {'mainT': mainT}),
            (r"/get_events", EventHandler, {'mainT': mainT}),
            (r"/News/(.*)", NewsHandler, {'mainT': mainT}),
            (r"/News", NewsHandler, {'mainT': mainT}),
            (r"/Search", SearchHandler, {'mainT': mainT}),
            (r"/get_news", SearchNewsHandler, {'mainT': mainT}),
            (r"/get_news/(.*)", SearchNewsHandler, {'mainT': mainT}),
            (r"/Audience", AudienceHandler, {'mainT': mainT}),
            (r"/previewNews", PreviewNewsHandler, {'mainT': mainT}),
            (r"/previewConversations", PreviewConversationHandler, {'mainT': mainT}),
            (r"/previewEvents", PreviewEventHandler, {'mainT': mainT}),
            (r"/sentiment", SentimentHandler, {'mainT': mainT}),
            (r"/bookmark", BookmarkHandler, {'mainT': mainT}),
            (r"/domain", DomainHandler, {'mainT': mainT}),
            (r"/newTweets", NewTweetsHandler, {'mainT': mainT}),
            (r"/newTweets/(.*)", NewTweetsHandler, {'mainT': mainT}),
            (r"/saveTopicId", TopicHandler, {'mainT': mainT}),
            (r"/api", DocumentationHandler, {'mainT': mainT}),
            (r"/api/v1\.1", Documentationv11Handler, {'mainT': mainT}),
            (r"/api/v1\.2", Documentationv12Handler, {'mainT': mainT}),
            (r"/api/get_themes", ThemesHandler, {'mainT': mainT}),
            (r"/api/get_influencers/(.*)/(.*)", InfluencersHandler, {'mainT': mainT}),
            (r"/api/get_feeds/(.*)/(.*)", FeedsHandler, {'mainT': mainT}),
            (r"/api/get_influencers/(.*)", InfluencersHandler, {'mainT': mainT}),
            (r"/api/get_feeds/(.*)", FeedsHandler, {'mainT': mainT}),
            (r"/getPages", PagesHandler, {'mainT': mainT}),
            (r"/api/v1.1/get_themes", ThemesV11Handler, {'mainT': mainT}),
            (r"/api/v1.1/get_feeds", FeedsV11Handler, {'mainT': mainT}),
            (r"/api/v1.1/get_influencers", InfluencersV11Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_topics", TopicsV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_news", NewsFeedsV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_audiences", AudiencesV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/search_news", NewsV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_events", EventV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_conversations", ConversationV12Handler, {'mainT': mainT}),
            (r"/api/v1.2/get_hashtags", HashtagsV12Handler, {'mainT': mainT}),
            (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)


class EventV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        topic_id = self.get_argument('topic_id', None)
        if topic_id is None:
            self.write({})
        date = self.get_argument('date', 'date')
        cursor = self.get_argument('cursor', '0')
        document = apiv12.getEvents(topic_id, date, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(document, indent=4))


class ConversationV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        if topic_id is None:
            self.write({})
        timeFilter = self.get_argument("date", "day")
        paging = self.get_argument("cursor", "0")
        docs = apiv12.getConversations(int(topic_id), timeFilter, paging)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps({'conversations': docs}, indent=4))


class TopicsV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        topics = apiv12.getTopics()
        self.set_header('Content-Type', 'application/json')
        self.write(topics)


class NewsFeedsV12Handler(BaseHandler, TemplateRendering):
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


class AudiencesV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        audiences = apiv12.getAudiences(topic_id)
        self.set_header('Content-Type', 'application/json')
        self.write(audiences)


class HashtagsV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        date = self.get_argument("date", "yesterday")
        hashtags = apiv12.getHastags(topic_id, date)
        self.set_header('Content-Type', 'application/json')
        self.write(hashtags)


class NewsV12Handler(BaseHandler, TemplateRendering):
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


class ThemesV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themes = apiv11.getThemes(4)
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class FeedsV11Handler(BaseHandler, TemplateRendering):
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


class InfluencersV11Handler(BaseHandler, TemplateRendering):
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


class ThemesHandler(BaseHandler, TemplateRendering):
    def get(self):
        themes = apiv1.getThemes()
        self.set_header('Content-Type', 'application/json')
        self.write(themes)


class InfluencersHandler(BaseHandler, TemplateRendering):
    def get(self, themename, cursor=None):
        influencers = apiv1.getInfluencers(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)


class FeedsHandler(BaseHandler, TemplateRendering):
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
            self.set_secure_cookie("userid", str(login_info['userid']))
            self.set_secure_cookie("username", str(username))
            logic.setCurrentTopic(str(login_info['userid']))
            self.write({'response': True, 'redirectUrl': self.get_argument('next', '/Topics')})
        else:
            self.write(json.dumps(login_info))


class LogoutHandler(BaseHandler, TemplateRendering):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")


class TopicsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        variables = {
            'title': "Topics",
            'alerts': logic.getAlertList(userid),
            'type': "alertlist",
            'alertlimit': logic.getAlertLimit(userid),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid=None):
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        userid = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            logic.deleteAlert(alertid, self.mainT, userid)
        elif posttype == u'stop':
            logic.stopAlert(alertid, self.mainT)
        elif posttype == u'start':
            logic.startAlert(alertid, self.mainT)
        elif posttype == u'publish':
            logic.publishAlert(alertid)
        elif posttype == u'unpublish':
            logic.unpublishAlert(alertid)

        template = "alerts.html"
        variables = {
            'title': "Topics",
            'alerts': logic.getAlertList(userid),
            'type': "alertlist",
            'alertlimit': logic.getAlertLimit(userid),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        }
        content = self.render_template(template, variables)
        self.write(content)


class CreateEditTopicHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid=None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {}
        variables['topic'] = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        variables['username'] = str(tornado.escape.xhtml_escape(self.get_current_username()))
        variables['alerts'] = logic.getAlertList(userid)

        if alertid != None:
            if logic.alertExist(userid):
                variables['title'] = "Edit Topic"
                variables['alert'] = logic.getAlert(alertid)
                variables['type'] = "editAlert"
            else:
                self.redirect("/Topics")
        else:
            if logic.getAlertLimit(userid) == 0:
                self.redirect("/Topics")
            variables['title'] = "Create Topic"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "createAlert"
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid=None):
        userid = tornado.escape.xhtml_escape(self.current_user)
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
            logic.updateAlert(alert, self.mainT, userid)
        else:
            alert['name'] = self.get_argument('alertname')
            logic.addAlert(alert, self.mainT, userid)
        self.redirect("/Topics")


class PreviewNewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'tweetsTemplate.html'
        keywords = self.get_argument("keywords")
        # exculdedkeywords = self.get_argument("excludedkeywords")
        languages = self.get_argument("languages")
        variables = {
            'tweets': logic.searchTweets(keywords, languages)
        }

        if len(variables['tweets']) == 0:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)


class BookmarkHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")

        variables = {
            'title': "Bookmark",
            'feeds': logic.getBookmarks(userid),
            'alertid': topic['topic_id'],
            'alerts': logic.getAlertList(userid),
            'alertname': topic['topic_name'],
            'type': "bookmark",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic
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
            content = logic.addBookmark(alert_id, user_id, link_id)
        else:
            content = logic.removeBookmark(alert_id, user_id, link_id)
        self.write(content)


class SentimentHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        if posttype == "positive":
            content = logic.sentimentPositive(alertid, user_id, link_id)
        elif posttype == "negative":
            content = logic.sentimentNegative(alertid, user_id, link_id)
        self.write(content)


class DomainHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        userid = tornado.escape.xhtml_escape(self.current_user)
        domain = self.get_argument("domain")
        logic.banDomain(userid, domain)
        self.write({})


# This handler gets all tweets about given topic
class FeedHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'

        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")

        tweets = logic.getTweets(topic['topic_id'])
        variables = {
            'title': "Feed",
            'alerts': logic.getAlertList(userid),
            'type': "feed",
            'tweets': tweets,
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
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
                'tweets': logic.getSkipTweets(alertid, lastTweetId)
            }
        else:
            template = 'alertFeed.html'
            alertid = self.get_argument('alertid')
            variables = {
                'tweets': logic.getTweets(alertid),
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
                'tweets': logic.getNewTweets(alertid, newestId)
            }
            content = self.render_template(template, variables)
        else:
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            content = str(logic.checkTweets(alertid, newestId))
        self.write(content)


class NewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")

        feeds = logic.getNews(topic['topic_id'], "yesterday", 0)
        variables = {
            'title': "News",
            'feeds': feeds['feeds'],
            'cursor': feeds['next_cursor'],
            'alertid': topic['topic_id'],
            'alerts': logic.getAlertList(userid),
            'alertname': topic['topic_name'],
            'type': "news",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        variables = {}
        if argument is not None:
            template = 'newsTemplate.html'
            alertid = self.get_argument('alertid')
            next_cursor = self.get_argument('next_cursor')
            try:
                date = self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            try:
                feeds = logic.getNews(alertid, date, int(next_cursor))
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
                feeds = logic.getNews(alertid, date, 0)
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
        userid = tornado.escape.xhtml_escape(self.current_user)
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


class AudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")

        audiences = logic.getAudiences(topic['topic_id'])
        variables = {
            'title': "Audience",
            'alertname': topic['topic_name'],
            'audiences': audiences,
            'alerts': logic.getAlertList(userid),
            'type': "audiences",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic
        }

        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        variables = {}
        template = 'alertAudience.html'
        alertid = self.get_argument('alertid')
        try:
            audiences = logic.getAudiences(alertid)
            variables = {
                'audiences': audiences,
                'alertid': alertid
            }
        except Exception as e:
            print(e)
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no audience now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)


class PagesHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'pages.html'
        keywordsList = self.get_argument("keywords").split(",")

        if keywordsList != ['']:
            sourceSelection = logic.sourceSelection(keywordsList)
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
        userid = tornado.escape.xhtml_escape(self.current_user)
        logic.saveTopicId(self.get_argument("topic_id"), userid)


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
        sources = logic.sourceSelection(keywordsList)

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
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Events",
            'alerts': logic.getAlertList(userid),
            'type': "events",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            "document": apiv12.getEvents(topic['topic_id'], "date", 0),
            'topic': topic
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
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        topic = logic.getCurrentTopic(tornado.escape.xhtml_escape(self.current_user))
        if topic is None:
            self.redirect("/topicinfo")
        variables = {
            'title': "Conversations",
            'alerts': logic.getAlertList(userid),
            'type': "conversation",
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            "docs": apiv12.getConversations(topic['topic_id'], "day", 0),
            'topic': topic
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


def main(mainT):
    tornado.options.parse_command_line()
    app = Application(mainT)
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()


def webserverInit(mainT):
    thr = Thread(target=main, args=[mainT])
    thr.daemon = True
    thr.start()
    thr.join()


if __name__ == "__main__":
    main()
