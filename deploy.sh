#!/bin/sh

eval $(cat .env | sed 's/^/export /')

echo "$(whoami)"

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

ufw allow 8484/tcp
ufw allow 27017/tcp
ufw allow 9181/tcp
ufw allow 5432/tcp

docker-compose down
docker-compose up -d

sleep 1m

echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} --password -d ${POSTGRESQL_DB} -a -f /data/schemas.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} --password -d ${POSTGRESQL_DB} -f /data/relevant_locations_data.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} --password -d ${POSTGRESQL_DB} -f /data/country_code_data.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} --password -d ${POSTGRESQL_DB} -f /data/location_country_codes_data.sql
