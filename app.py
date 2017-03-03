import tornado.web
import tornado.options
import tornado.ioloop
import logic
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from threading import Thread
import os
import string
import random
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')

chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')
secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(100)])
print secret_key

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=False,
    cookie_secret= secret_key,
    login_url= "/login",
)

class TemplateRendering:
    def render_template(self, template_name, variables):
        env = Environment(loader = FileSystemLoader(settings['template_path']))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        content = template.render(variables)
        return content

class Application(tornado.web.Application):
    def __init__(self, mainT):
        handlers = [
            (r"/", MainHandler, {'mainT':mainT}),
            (r"/logout", LogoutHandler, {'mainT': mainT}),
            (r"/login", LoginHandler, {'mainT':mainT}),
            (r"/Alerts", AlertsHandler, {'mainT':mainT}),
            (r"/Alerts/([0-9])", AlertsHandler, {'mainT':mainT}),
            (r"/alertinfo", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/alertinfo/([0-9])", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/Feed/(.*)", FeedHandler, {'mainT':mainT}),
            (r"/Feed", FeedHandler, {'mainT':mainT}),
            (r"/preview", PreviewHandler, {'mainT':mainT}),
            (r"/newTweets", NewTweetsHandler, {'mainT':mainT}),
            (r"/newTweets/(.*)", NewTweetsHandler, {'mainT':mainT}),
            (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, mainT):
        self.mainT = mainT

    def get_current_user(self):
        return self.get_secure_cookie("userid")

class MainHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'index.html'
        variables = {
            'title' : "Watchtower"
        }
        content = self.render_template(template, variables)
        self.write(content)

class LoginHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'login.html'
        variables = {
            'title' : "Login Page"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self):
        userinfo = logic.getUserInfo(self.get_argument("username"))
        print type(userinfo['userid'])
        userInputPassword = str(self.get_argument("password"))
        if userInputPassword == userinfo['password']:
            self.set_secure_cookie("userid", str(userinfo['userid']))
            self.redirect(self.get_argument('next', '/Alerts'))
        else:
            self.write("Information is not correct")

class LogoutHandler(BaseHandler, TemplateRendering):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")

class AlertsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid = None):
        logic.refrestAlertStatus(self.mainT)
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid)
        }
        if alertid != None:
            info = logic.response(alertid)
            variables['message'] = info['message']
            variables['messagetype'] = info['type']
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid = None):
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        userid = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            print posttype, type(posttype)
            info = logic.deleteAlert(alertid, self.mainT,userid)
        elif posttype == u'stop':
            print "stop", alertid, posttype
            info = logic.stopAlert(alertid, self.mainT)
        else:
            print "start"
            info = logic.startAlert(alertid, self.mainT)
        template = "alerts.html"
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid)
        }
        variables['message'] = info['message']
        variables['messagetype'] = info['type']
        content = self.render_template(template, variables)
        self.write(content)

class CreateEditAlertsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {}
        if alertid != None:
            variables['title'] = "Edit Alert"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "editAlert"
        else:
            print logic.getAlertLimit(userid)
            if logic.getAlertLimit(userid) == 0:
                self.redirect("/Alerts")
            variables['title'] = "Create Alert"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "createAlert"
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        alert = {}
        alert['keywords'] = ",".join(self.get_argument("keywords").split(","))
        keywordlimit = 10 - len(self.get_argument("keywords").split(","))
        alert['keywordlimit'] = keywordlimit
        alert['excludedkeywords'] = ",".join(self.get_argument("excludedkeywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = ",".join(self.request.arguments.get("languages"))
        else:
            alert['lang'] = ""
        if alertid != None:
            alert['alertid'] = alertid
            logic.updateAlert(alert, self.mainT, userid)
        else:
            alert['name'] = self.get_argument('alertname')
            alertid = logic.getNextAlertId()
            logic.addAlert(alert, self.mainT, userid)
        self.redirect("/Alerts/" + str(alertid))

class PreviewHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        template = 'tweetsTemplate.html'
        keywords = self.get_argument("keywords")
        exculdedkeywords = self.get_argument("excludedkeywords")
        languages = self.get_argument("languages")
        variables = {
            'tweets': logic.searchTweets(keywords, languages)
        }
        content = self.render_template(template, variables)
        self.write(content)

class FeedHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, scroll = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title': "Feed",
            'alerts': logic.getAlertList(userid),
            'type': "feed"
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, scroll=None):
        if scroll is not None:
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
        content = self.render_template(template, variables)
        self.write(content)

class NewTweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self, get = None):
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

def main(mainT):
    tornado.options.parse_command_line()
    app = Application(mainT)
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()

def webserverInit(mainT):
    thr = Thread(target= main, args= [mainT] )
    thr.daemon = True
    thr.start()
    thr.join()

if __name__ == "__main__":
    main()
