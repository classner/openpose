#!/bin/bash
#
# This script starts a container with a postgres database
#

# find the scripts directory
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

sudo docker run --name "${PROJECT_NAME}-data" -v ${DB_DIR}:/var/lib/postgresql/data -d postgres
