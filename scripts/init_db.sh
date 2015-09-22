#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo "CREATE USER \"${DB_USER}\" WITH LOGIN PASSWORD '${DB_PASS}'" | psql -U postgres -h "${DB_HOST}" -p "${DB_PORT}" -U postgres
createdb -U postgres -h "${DB_HOST}" -p "${DB_PORT}" --owner=${DB_USER} --encoding=UTF8 ${DB_NAME}

python ./server/manage.py syncdb --noinput
python ./server/manage.py migrate menu
python ./server/manage.py migrate dashboard
python ./server/manage.py migrate django_extensions
python ./server/manage.py migrate captcha
python ./server/manage.py migrate common
python ./server/manage.py migrate accounts
python ./server/manage.py migrate licenses
python ./server/manage.py migrate mturk
python ./server/manage.py migrate photos
python ./server/manage.py migrate segmentation 0002
python ./server/manage.py migrate pose
python ./server/manage.py migrate segmentation

python ./server/manage.py createsuperuser
python ./server/manage.py createcachetable db-cache
