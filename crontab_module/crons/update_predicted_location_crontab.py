import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))
from predict_location.update_field_db import update_field_db as up_db

database_name = "audience_test"
field_name = "location"

up_db(database_name, field_name)