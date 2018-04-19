import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))
from predict_location.update_field_db import update_field_db as up_db

database_names = ["audience_test", "events"]
field_names = ["location", "place"]

for ind in range(len(database_names)):
    up_db(database_names[ind], field_names[ind])
