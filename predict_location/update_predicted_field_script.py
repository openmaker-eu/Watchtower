from update_field_db import update_field_db as up_db
import sys

if(len(sys.argv) != 4):
    print(
        """Missing command line arguments. Usage:

            python update_predicted_field.py "host" "database_name" "field_name"
        """
    )
    sys.exit(0)

host = sys.argv[1]
database_name = sys.argv[2]
field_name = sys.argv[3]

up_db(host, database_name, field_name)


