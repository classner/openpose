#!/bin/bash
#
# Install all the packages used by the server
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

source $DIR/load_config.sh
cd "$REPO_DIR"

#########################

echo "Installing node.js..."

# fix npm registry
echo "Uninstall old node"
apt-get remove -y nodejs npm
rm -f /usr/bin/coffee /usr/local/bin/coffee
rm -f /usr/bin/lessc /usr/local/bin/lessc

echo "Install newest node"
#sudo add-apt-repository ppa:chris-lea/node.js
add-apt-repository -y ppa:richarvey/nodejs
apt-get update -y
apt-get install -y nodejs npm

nodejs -v

# some naming issues
ln -s /usr/bin/nodejs /usr/bin/node

npm config set registry http://registry.npmjs.org/
echo "Install coffeescript"
npm install -g coffee-script
echo "Install less"
npm install -g less

#########################

echo "$0: done"
