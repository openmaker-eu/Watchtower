"""
Tweet Handlers for Watchtower
"""

__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web

from handlers.base import BaseHandler
from handlers.base import TemplateRendering

from logic.helper import get_relevant_locations
from logic.topics import get_topic_list
from logic.tweets import update_publish_tweet, get_tweet, get_twitter_user, get_publish_tweet, get_publish_tweets, \
    delete_publish_tweet
from logic.tweets_feed import get_new_tweets, check_tweets
from logic.users import get_current_topic, get_current_location, get_topic_limit


class NewTweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self, get=None):
        if get is not None:
            template = 'tweetsTemplate.html'
            topic_id = self.get_argument('alertid')
            newest_id = self.get_argument('tweetid')
            variables = {
                'tweets': get_new_tweets(topic_id, newest_id)
            }
            content = self.render_template(template, variables)
        else:
            topic_id = self.get_argument('alertid')
            newest_id = self.get_argument('tweetid')
            content = str(check_tweets(topic_id, newest_id))
        self.write(content)


class RedirectHandler(BaseHandler, TemplateRendering):
    def get(self):
        user_agent = self.request.headers["User-Agent"] if "User-Agent" in self.request.headers else ""
        tweet_id = int(self.get_argument("tweet_id", -1))
        topic_id = int(self.get_argument("topic_id", -1))
        tweet = get_tweet(topic_id, tweet_id)

        template = 'redirect.html'
        variables = {
            'title': "Redirect Page",
            'tweet': tweet
        }
        content = self.render_template(template, variables)
        self.write(content)


class TweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, tweet_id=None):
        user_id = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        changing_topic = int(self.get_argument("topic_id", -1))
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        location = get_current_location(tornado.escape.xhtml_escape(self.current_user))
        if changing_topic != -1:
            topic['topic_id'] = changing_topic
            template = 'renderTweets.html'
        relevant_locations = get_relevant_locations()
        new_tweet = False
        if tweet_id is not None:
            news_id = int(self.get_argument("news_id", -1))
            date = self.get_argument("date", "")
            new_tweet = int(tweet_id) == -1
            if new_tweet:
                twitter_user = get_twitter_user(user_id)
                if twitter_user['twitter_id'] == '':
                    self.redirect("/twitter_auth")
            sub_type = "item"
            tweets = get_publish_tweet(topic['topic_id'], user_id, tweet_id, news_id, date)
        else:
            status = int(self.get_argument("status", 0))
            request_type = self.get_argument("request_type", "")
            if request_type == 'ajax':
                template = 'renderTweets.html'
            sub_type = "list"
            tweets = get_publish_tweets(topic['topic_id'], user_id, status)
        twitter_user = get_twitter_user(user_id)
        variables = {
            'title': "Tweets",
            'alerts': get_topic_list(user_id),
            'type': "tweets",
            'sub_type': sub_type,
            'new_tweet': new_tweet,
            'alertlimit': get_topic_limit(user_id),
            'username': str(tornado.escape.xhtml_escape(self.get_current_username())),
            'topic': topic,
            'location': location,
            'relevant_locations': relevant_locations,
            'tweets': tweets,
            'twitter_user': twitter_user
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, tweet_id=None):
        topic = get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        tweet_id = self.get_argument("tweet_id")
        posttype = self.get_argument("posttype")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            delete_publish_tweet(topic['topic_id'], user_id, tweet_id)
        elif posttype == u'update':
            news_id = self.get_argument("news_id")
            date = self.get_argument("date")
            title = self.get_argument("title")
            description = self.get_argument("tweet_link_description")
            text = self.get_argument("text")
            image_url = self.get_argument("image_url")
            update_publish_tweet(topic['topic_id'], user_id, tweet_id, date, text, news_id, title, description,
                                       image_url)
        if tweet_id is not None:
            self.redirect("/Tweets")
        else:
            self.write({'response': True})
