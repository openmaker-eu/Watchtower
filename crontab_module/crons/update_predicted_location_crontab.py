import sys
from decouple import config
sys.path.insert(0, config("ROOT_DIR"))
from predict_location.update_field_db import update_field_db as up_db

if(len(sys.argv) != 2):
    print(
        """Missing command line arguments. Usage:

            python update_predicted_field.py "host_ip"
        """
    )
    sys.exit(0)

host = sys.argv[1]
database_name = "audience_test"
field_name = "location"

up_db(host, database_name, field_name)


