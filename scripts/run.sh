#!/bin/bash
#
# This script runs everything.
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

touch $REPO_DIR/nginx-access.log

service rabbitmq-server start
service memcached start
service supervisor start
supervisorctl start ${PROJECT_NAME}
service nginx start
bash "$DIR/start_worker.sh" &
