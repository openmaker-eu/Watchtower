from datetime import datetime
from time import time

import bson.objectid


def determine_date(date):
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'month':
        return str(current_milli_time - 30 * one_day)
    return '0'


def date_formatter(x):
    if isinstance(x, datetime):
        return x.strftime("%d-%m-%Y")
    elif isinstance(x, bson.objectid.ObjectId):
        return str(x)
    else:
        raise TypeError(x)

def tweet_date_to_string(x):
    if isinstance(x, datetime):
        return x.strftime("%I:%M %p - %b %d, %Y GMT")
    elif isinstance(x, str):
        return datetime.strptime(x, "%I:%M %p - %b %d, %Y %Z")
