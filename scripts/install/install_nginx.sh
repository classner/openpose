#!/bin/bash
#
# Set up nginx and gunicorn
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

# create a new installation
bash "$DIR/make_public.sh"

echo "$0: done"
