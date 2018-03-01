"""
This is the settings file for Watchtower.
"""
__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

# import random
# import string
import os

# chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace(
#     '\\', '')
# secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(100)])
secret_key = 'PEO+{+RlTK[3~}TS-F%[9J/sIp>W7!r*]YV75GZV)e;Q8lAdNE{m@oWK.+u-&z*-p>~Xa!Z8j~{z,BVv.e0GChY{(1.KVForO#rQ'

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=False,
    cookie_secret=secret_key,
    login_url="/login",
)