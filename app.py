import tornado.web
import tornado.options
import tornado.ioloop
from tornado.escape import json_encode
import logic, api, newapi
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from threading import Thread
import os
import string
import random
import json

chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')
secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(100)])
secret_key = 'PEO+{+RlTK[3~}TS-F%[9J/sIp>W7!r*]YV75GZV)e;Q9lAdNE{m@oWX.+u-&z*-p>~Xa!Z8j~{z,BVv.e0GChY{(1.KVForO#rQ'

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

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, mainT):
        self.mainT = mainT

    def get_current_user(self):
        return self.get_secure_cookie("userid")

class Application(tornado.web.Application):
    def __init__(self, mainT):
        handlers = [
            (r"/", MainHandler, {'mainT':mainT}),
            (r"/logout", LogoutHandler, {'mainT': mainT}),
            (r"/login", LoginHandler, {'mainT':mainT}),
            (r"/Alerts", AlertsHandler, {'mainT':mainT}),
            #(r"/message", MessageHandler, {'mainT':mainT}),
            (r"/alertinfo", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/alertinfo/([0-9]*)", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/Feed/(.*)", FeedHandler, {'mainT':mainT}),
            (r"/Feed", FeedHandler, {'mainT':mainT}),
            (r"/News/(.*)", NewsHandler, {'mainT':mainT}),
            (r"/News", NewsHandler, {'mainT':mainT}),
            (r"/preview", PreviewHandler, {'mainT':mainT}),
            (r"/newTweets", NewTweetsHandler, {'mainT':mainT}),
            (r"/newTweets/(.*)", NewTweetsHandler, {'mainT':mainT}),
            (r"/api", DocumentationHandler, {'mainT':mainT}),
            (r"/api/v1\.1", Documentationv11Handler, {'mainT':mainT}),
            (r"/api/get_themes", ThemesHandler, {'mainT':mainT}),
            (r"/api/get_influencers/(.*)/(.*)", InfluencersHandler, {'mainT':mainT}),
            (r"/api/get_feeds/(.*)/(.*)", FeedsHandler, {'mainT':mainT}),
            (r"/api/get_influencers/(.*)", InfluencersHandler, {'mainT':mainT}),
            (r"/api/get_feeds/(.*)", FeedsHandler, {'mainT':mainT}),
            (r"/api/v1.1/get_themes", ThemesV11Handler, {'mainT':mainT}),
            (r"/api/v1.1/get_feeds", FeedsV11Handler, {'mainT':mainT}),
            (r"/api/v1.1/get_influencers", InfluencersV11Handler, {'mainT':mainT}),
            (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)

class ThemesV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themes = newapi.getThemes(4)
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
        feeds = newapi.getFeeds(themename, themeid , 4, date, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

class InfluencersV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        feeds = newapi.getInfluencers(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

class DocumentationHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'api.html'
        variables = {
            'title' : "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)

class Documentationv11Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv11.html'
        variables = {
            'title' : "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)

class ThemesHandler(BaseHandler, TemplateRendering):
    def get(self):
        themes = logic.getThemes()
        self.set_header('Content-Type', 'application/json')
        self.write(themes)

class InfluencersHandler(BaseHandler, TemplateRendering):
    def get(self, themename, cursor=None):
        influencers = logic.getInfluencers(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)

class FeedsHandler(BaseHandler, TemplateRendering):
    def get(self, themename, cursor=None):
        feeds = logic.getFeeds(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

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
        userinfo = logic.getUserInfo(str(self.get_argument("username")))
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
    def get(self):
        self.mainT.checkThread()
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid),
            'threadstatus': logic.getThreadStatus(self.mainT),
            'threadconnection': logic.getThreadConnection(self.mainT)
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid = None):
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        userid = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            info = logic.deleteAlert(alertid, self.mainT,userid)
        elif posttype == u'stop':
            info = logic.stopAlert(alertid, self.mainT)
        elif posttype == u'start':
            info = logic.startAlert(alertid, self.mainT)
        elif posttype == u'publish':
            info = logic.publishAlert(alertid)
        elif posttype == u'unpublish':
            info = logic.unpublishAlert(alertid)
        template = "alerts.html"
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid)
        }
        content = self.render_template(template, variables)
        self.write(content)

class MessageHandler(BaseHandler, TemplateRendering):
    def post(self):
        alertid = self.get_argument("alertid")
        info = logic.response(alertid)
        result = info['message'] + ";" + info['type']
        self.write(result)

class CreateEditAlertsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {}
        if alertid != None:
            if logic.alertExist(alertid):
                if logic.checkUserIdAlertId(userid, alertid):
                    variables['title'] = "Edit Alert"
                    variables['alert'] = logic.getAlert(alertid)
                    variables['type'] = "editAlert"
                else:
                    self.redirect("/Alerts")
            else:
                self.redirect("/Alerts")
        else:
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
        alert['description'] = self.get_argument("description")
        keywordlimit = 10 - len(self.get_argument("keywords").split(","))
        alert['keywordlimit'] = keywordlimit
        #alert['excludedkeywords'] = ",".join(self.get_argument("excludedkeywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = b','.join(self.request.arguments.get("languages")).decode("utf-8") 
        else:
            alert['lang'] = ""
        if alertid != None:
            alert['alertid'] = alertid
            logic.updateAlert(alert, self.mainT, userid)
        else:
            alert['name'] = self.get_argument('alertname')
            alertid = logic.getNextAlertId()
            logic.addAlert(alert, self.mainT, userid)
        self.redirect("/Alerts")

class PreviewHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        template = 'tweetsTemplate.html'
        keywords = self.get_argument("keywords")
        #exculdedkeywords = self.get_argument("excludedkeywords")
        languages = self.get_argument("languages")
        variables = {
            'tweets': logic.searchTweets(keywords, languages)
        }
        if len(variables['tweets']) == 0:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)

class FeedHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        if argument is not None:
            try:
                alertid = int(argument)
                variables = {
                    'title': "Feed",
                    'tweets': logic.getTweets(alertid),
                    'alertid': alertid,
                    'alertname': logic.getAlertName(alertid),
                    'comesAlert': True,
                    'type': "feed"
                }
                if len(variables['tweets']) == 0:
                    self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
            except ValueError:
                variables = {
                    'title': "Feed",
                    'alerts': logic.getAlertList(userid),
                    'comesAlert': False,
                    'type': "feed"
                }
                pass
        else:
            variables = {
                'title': "Feed",
                'alerts': logic.getAlertList(userid),
                'comesAlert': False,
                'type': "feed"
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

class NewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        if argument is not None:
            try:
                alertid = int(argument)
                try:
                    date =  self.get_argument('date')
                except:
                    date = 'yesterday'
                    pass
                feeds = logic.getNews(alertid, date, 0)
                variables = {
                    'title': "News",
                    'feeds': feeds['feeds'],
                    'cursor': feeds['next_cursor'],
                    'alertid': alertid,
                    'alertname': logic.getAlertName(alertid),
                    'comesAlert': True,
                    'type': "news"
                }
                if len(variables['feeds']) == 0:
                    self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
            except ValueError:
                variables = {
                    'title': "News",
                    'alerts': logic.getAlertList(userid),
                    'comesAlert': False,
                    'type': "news"
                }
                pass
        else:
            variables = {
                'title': "News",
                'alerts': logic.getAlertList(userid),
                'comesAlert': False,
                'type': "news"
            }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        if argument is not None:
            template = 'newsTemplate.html'
            alertid = self.get_argument('alertid')
            next_cursor = self.get_argument('next_cursor')
            try:
                date =  self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            feeds = logic.getNews(alertid, date, int(next_cursor))
            variables = {
                'feeds': feeds['feeds'],
                'cursor': feeds['next_cursor'],
            }
        else:
            template = 'alertNews.html'
            alertid = self.get_argument('alertid')
            try:
                date =  self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            feeds = logic.getNews(alertid, date, 0)
            variables = {
                'feeds': feeds['feeds'],
                'cursor': feeds['next_cursor'],
                'alertid': alertid
            }
            if len(variables['feeds']) == 0:
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no feed now.</b></p>")
        content = self.render_template(template, variables)
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
