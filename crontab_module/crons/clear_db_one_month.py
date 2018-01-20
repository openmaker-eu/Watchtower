import datetime
import sys

sys.path.insert(0,'/root/cloud')
sys.path.insert(0,'/root/.local/share/virtualenvs/cloud-rP5jkfQF/lib/python3.5/site-packages/')

import dateutil.relativedelta
from application.Connections import Connection
from bson import ObjectId

prev_month_datetime = datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
prev_two_week_datetime = datetime.datetime.now() + dateutil.relativedelta.relativedelta(weeks=-2)
prev_month_objectid = ObjectId.from_datetime(prev_month_datetime)
prev_two_week_objectid = ObjectId.from_datetime(prev_two_week_datetime)

print(prev_month_objectid)

for topic_id in Connection.Instance().db.collection_names():
    if topic_id != "counters":
        Connection.Instance().db[str(topic_id)].remove({'_id': {'$lte': prev_two_week_objectid}})
        Connection.Instance().db.command("compact", str(topic_id))

'''
Deletes certain fields from user profiles in all_audience to reduce total size of the collection.
'''
def compress_audience_data():
    # remove unwanted fields from all objects
    print("Compressing audience data...")
    Connection.Instance().audienceDB['all_audience'].update({}, {'$unset': {
        "profile_background_color": 1,
        "default_profile_image": 1,
        "id_str": 1,
        "contributors_enabled": 1,
        "profile_sidebar_border_color": 1,
        "profile_use_background_image": 1,
        "profile_background_image_url": 1,
        "protected": 1,
        "translator_type": 1,
        "notifications": 1,
        "following": 1,
        "default_profile": 1,
        "is_translator": 1,
        "has_extended_profile": 1,
        "profile_image_url": 1,
        "timezone": 1,
        "follow_request_sent": 1,
        "profile_background_tile": 1,
        "is_translation_enabled": 1,
        "status": 1,
        "profile_text_color": 1,
        "profile_sidebar_fill_color": 1,
        "profile_link_color": 1
    }}, multi=True)
    Connection.Instance().audienceDB.command({'compact': 'all_audience'})


compress_audience_data()
