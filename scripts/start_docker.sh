#!/bin/bash
#
# This script starts the openpose container.
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

sudo docker run -t -i -p 45001:80 --link "${PROJECT_NAME}-data:${DB_HOST}" \
  -v ${REPO_DIR}/media:/home/appuser/data/media "${PROJECT_NAME}" /bin/bash
