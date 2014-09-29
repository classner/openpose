#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

python $SRC_DIR/manage.py syncdb
python $SRC_DIR/manage.py migrate
python $SRC_DIR/manage.py createsuperuser
python $SRC_DIR/manage.py createcachetable db-cache
