"""
Tweet Handlers for Watchtower
"""
__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

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
        user_agent = self.request.headers["User-Agent"]
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

