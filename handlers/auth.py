"""
Auth Handlers for Watchtower
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web
import tornado.escape
import json
from decouple import config

from handlers.base import BaseHandler, TemplateRendering
import logic


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
        register_info = logic.register(str(username), password, country.lower())
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
        update_info = logic.update_user(user_id, password, country.lower(), auth_token, twitter_pin)
        if update_info['response']:
            self.write({'response': True, 'redirectUrl': '/Topics'})
        else:
            self.write(json.dumps(update_info))


# class FacebookAuthHandler(BaseHandler, TemplateRendering):
#     @tornado.web.authenticated
#     def post(self):
#         print("In Facebook Auth Handler")
#         AUTH_URL = "https://www.facebook.com/v2.12/dialog/oauth"
#         state = 0  # generate a random string
#         params = {
#             'client_id': config('FACEBOOK_CLIENT_ID'),
#             'redirect_uri': self.get_argument('redirect_uri'),
#             'state': state
#         }



class TwitterAuthHandler(BaseHandler, TemplateRendering):
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
            'title': "Twitter Auth",
            'type': "twitterAuth",
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
        twitter_pin = self.get_argument("twitter_pin", "")
        user_id = tornado.escape.xhtml_escape(self.current_user)
        auth_token = self.get_secure_cookie("request_token")
        self.clear_cookie("request_token")
        update_info = logic.update_twitter_auth(user_id, auth_token, twitter_pin)
        if update_info['response']:
            self.write({'response': True, 'redirectUrl': '/Topics'})
        else:
            self.write({'response': False})