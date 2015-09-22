#!/bin/bash
#
# This script completely sets up the OpenSurfaces database and server
#
# Usage: ./install_all.sh
#

# load configuration info
set -e
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )/.." && pwd )"
source "$DIR/load_config.sh"

echo ""
echo "===================================================================="

bash "${DIR}/scripts/install/install_packages.sh"
bash "${DIR}/scripts/install/install_nodejs.sh"
bash "${DIR}/scripts/install/install_python.sh"
bash "${DIR}/scripts/install/install_memcached.sh"
bash "${DIR}/scripts/install/install_server.sh"
bash "${DIR}/scripts/install/install_nginx.sh"
