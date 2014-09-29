#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo "Creating directories..."
mkdir -p $DATA_DIR/media
mkdir -p $DATA_DIR/static
mkdir -p run
mkdir -p $BACKUP_DIR

echo "Fixing permissions..."
bash "$DIR/fix_permissions.sh" appuser

echo "Fixing celerybeat-schedule..."
rm -f $SRC_DIR/celerybeat-schedule

echo "Cleaning old static files..."
rm -rf $DATA_DIR/static/*

echo "$0: done"
