#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo "CREATE USER \"${DB_USER}\" WITH LOGIN PASSWORD '${DB_PASS}'" | psql -U postgres -h "${DB_HOST}" -p "${DB_PORT}" -U postgres
createdb -U postgres -h "${IP}" -p "${PORT}" -U postgres --owner=${DB_USER} --encoding=UTF8 ${DB_NAME}

python ./server/manage.py syncdb
python ./server/manage.py migrate
python ./server/manage.py createsuperuser
python ./server/manage.py createcachetable db-cache
