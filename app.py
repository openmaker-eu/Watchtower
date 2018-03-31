"""
Watchtower Web Server
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli', 'Baris Esmer']

import tornado.ioloop
from tornado.options import options
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
    options.parse_command_line()
    app = WatchtowerApp()
    try:
        if config("SENTRY_TOKEN") != 'null':
            app.sentry_client = AsyncSentryClient(config("SENTRY_TOKEN"))
    except RuntimeError as err:
        logger.log_and_print(err)
        pass

    try:
        app.listen(options.port)
        logger.log_and_print("Listening on port " + str(options.port))
    except SystemError as err:
        logger.log_and_print(err)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
