#!/bin/bash
#
# Install all the packages used by the server
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

source $DIR/load_config.sh
cd "$REPO_DIR"

set -e

#########################

echo "Installing packages..."

# install ubuntu packages
apt-get update -y
apt-get install -y $(cat $DIR/install/requirements-packages.txt)

# install dependencies for numpy/scipy
apt-get build-dep -y python-numpy python-scipy

# make sure the image libraries are in /usr/lib
[[ -f /usr/lib/libfreetype.so ]] || ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
[[ -f /usr/lib/libjpeg.so ]] || ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
[[ -f /usr/lib/libz.so ]] || ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
[[ -f /usr/lib/liblcms.so ]] || ln -s /usr/lib/`uname -i`-linux-gnu/liblcms.so /usr/lib/

#########################

echo "$0: done"
