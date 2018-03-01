"""
Watchtower Web Server
"""
__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar', 'Baris Esmer']

import tornado.ioloop
import tornado.options
import tornado.web

from raven.contrib.tornado import AsyncSentryClient
from decouple import config

from settings import settings
from urls import url_patterns
from application.utils.general import Logger

logger = Logger('watchtower.' + __name__ + '.log')


class WatchtowerApp(tornado.web.Application):
    def __init__(self):
        super(WatchtowerApp, self).__init__(url_patterns, **settings, autoreload=True)


def main():
    tornado.options.parse_command_line()
    app = WatchtowerApp()
    try:
        app.sentry_client = AsyncSentryClient(config("SENTRY_TOKEN"))
    except RuntimeError as err:
        logger.log_and_print(err)
        pass
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
