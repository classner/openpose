#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

IP=$(sudo docker inspect --format '{{ .NetworkSettings.IPAddress }}' openpose-data)
PORT=$(sudo docker inspect --format '{{ .Config.ExposedPorts }}' openpose-data | sed 's#^[^[:digit:]]*\([[:digit:]]*\)/tcp.*$#\1#')
echo "CREATE USER \"${DB_USER}\" WITH LOGIN PASSWORD '${DB_PASS}'" | psql -U postgres -h "${IP}" -p "${PORT}" -U postgres
createdb -U postgres -h "${IP}" -p "${PORT}" -U postgres --owner=labelmaterial --encoding=UTF8 labelmaterial

python ./server/manage.py syncdb
python ./server/manage.py migrate
python ./server/manage.py createsuperuser
python ./server/manage.py createcachetable db-cache
