import tornado.web
import tornado.escape

from handlers.base import BaseHandler, TemplateRendering, Api500ErrorHandler
from apis import apiv1, apiv11, apiv12, apiv13


class ChallengeV13Handler(BaseHandler, TemplateRendering):
    def get(self):
        is_open = bool(self.get_argument('is_open', False))
        date = str(self.get_argument("date", ""))
        try:
            cursor = int(self.get_argument('cursor', '0'))
            if cursor < 0:
                cursor = 0
        except:
            cursor = 0
            pass
        challenges = apiv13.getChallenges(is_open, date, int(cursor))
        self.set_header('Content-Type', 'application/json')
        self.write(challenges)
