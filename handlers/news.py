"""
News Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape
import json

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13
import logic


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


class SentimentHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alertid = self.get_argument("alertid")
        rating = self.get_argument("rating")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        logic.sentiment_news(alertid, user_id, link_id, rating)
        self.write("")


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


class DomainHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        domain = self.get_argument("domain")
        alertid = self.get_argument("alertid")
        logic.ban_domain(user_id, alertid, domain)
        self.write({})


'''
API handlers
'''


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


class FeedsHandler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self, themename, cursor=None):
        feeds = apiv1.getFeeds(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)


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


class HashtagsV12Handler(BaseHandler, TemplateRendering, Api500ErrorHandler):
    def get(self):
        topic_id = self.get_argument("topic_id", None)
        date = self.get_argument("date", "yesterday")
        hashtags = apiv12.getHastags(topic_id, date)
        self.set_header('Content-Type', 'application/json')
        self.write(hashtags)

