#!/bin/bash
#
# This script completely sets up the OpenSurfaces database and server
#
# Usage: ./install_all.sh
#

# load configuration info
set -e
source "scripts/load_config.sh"

echo ""
echo "===================================================================="
echo "Now creating docker image."
REV=`git rev-parse HEAD`
docker build -t "${PROJECT_NAME}:${REV}" .
docker tag "${PROJECT_NAME}:${REV}" "${PROJECT_NAME}:latest"

# exit message
echo "$0: done!"
echo ""
echo "===================================================================="
