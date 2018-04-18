"""
Tweet Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web

from handlers.base import BaseHandler
from handlers.base import TemplateRendering
import logic


class NewTweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self, get=None):
        if get is not None:
            template = 'tweetsTemplate.html'
            topic_id = self.get_argument('alertid')
            newest_id = self.get_argument('tweetid')
            variables = {
                'tweets': logic.get_new_tweets(topic_id, newest_id)
            }
            content = self.render_template(template, variables)
        else:
            topic_id = self.get_argument('alertid')
            newest_id = self.get_argument('tweetid')
            content = str(logic.check_tweets(topic_id, newest_id))
        self.write(content)


class RedirectHandler(BaseHandler, TemplateRendering):
    def get(self):
        user_agent = self.request.headers["User-Agent"] if "User-Agent" in self.request.headers else ""
        tweet_id = int(self.get_argument("tweet_id", -1))
        topic_id = int(self.get_argument("topic_id", -1))
        tweet = logic.get_tweet(topic_id, tweet_id)

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
            if new_tweet:
                twitter_user = logic.get_twitter_user(user_id)
                if twitter_user['twitter_id'] == '':
                    self.redirect("/twitter_auth")
            sub_type = "item"
            tweets = logic.get_publish_tweet(topic['topic_id'], user_id, tweet_id, news_id, date)
        else:
            status = int(self.get_argument("status", 0))
            request_type = self.get_argument("request_type", "")
            if request_type == 'ajax':
                template = 'renderTweets.html'
            sub_type = "list"
            tweets = logic.get_publish_tweets(topic['topic_id'], user_id, status)
        twitter_user = logic.get_twitter_user(user_id)
        variables = {
            'title': "Tweets",
            'alerts': logic.get_topic_list(user_id),
            'type': "tweets",
            'sub_type': sub_type,
            'new_tweet': new_tweet,
            'alertlimit': logic.get_topic_limit(user_id),
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
        topic = logic.get_current_topic(tornado.escape.xhtml_escape(self.current_user))
        tweet_id = self.get_argument("tweet_id")
        posttype = self.get_argument("posttype")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            logic.delete_publish_tweet(topic['topic_id'], user_id, tweet_id)
        elif posttype == u'update':
            news_id = self.get_argument("news_id")
            date = self.get_argument("date")
            title = self.get_argument("title")
            description = self.get_argument("tweet_link_description")
            text = self.get_argument("text")
            image_url = self.get_argument("image_url")
            logic.update_publish_tweet(topic['topic_id'], user_id, tweet_id, date, text, news_id, title, description,
                                       image_url)
        if tweet_id is not None:
            self.redirect("/Tweets")
        else:
            self.write({'response': True})
