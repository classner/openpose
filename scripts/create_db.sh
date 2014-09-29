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

sudo docker run --name openpose-data -v ${REPO_DIR}/db:/var/lib/postgresql/data -d postgres
