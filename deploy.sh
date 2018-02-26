#!/bin/sh

eval $(cat .env | sed 's/^/export /')

docker-compose down
docker-compose up -d

echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} --password -d ${POSTGRESQL_DB} -a -f /data/schemas.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} -d ${POSTGRESQL_DB} -f /data/relevant_locations_data.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} -d ${POSTGRESQL_DB} -f /data/country_code_data.sql
echo ${POSTGRESQL_PASSWORD} | docker exec -i postgres psql -h ${HOST_IP} -U ${POSTGRESQL_USER} -d ${POSTGRESQL_DB} -f /data/location_country_codes_data.sql
