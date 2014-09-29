#!/bin/bash
#
# This script starts a container with a postgres database
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

#!/bin/bash

set -e

CID=$(sudo docker run --name openpose-data -d postgres)
sleep 3

IP=$(sudo docker inspect --format '{{ .NetworkSettings.IPAddress }}' "${CID}")
PORT=$(sudo docker inspect --format '{{ .Config.ExposedPorts }}' openpose-data | sed 's#^[^[:digit:]]*\([[:digit:]]*\)/tcp.*$#\1#')
echo "CREATE USER \"${DB_USER}\" WITH LOGIN PASSWORD '${DB_PASS}'" | psql -U postgres -h "${IP}" -p "${PORT}" -U postgres
createdb -U postgres -h "${IP}" -p "${PORT}" -U postgres --owner=labelmaterial --encoding=UTF8 labelmaterial
