#!/bin/bash
#
# This script sets up directories and fixes permissions
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

# give it some time to start
tail -f $REPO_DIR/nginx-access.log
