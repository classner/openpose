#!/bin/bash
#
# Set up the server config.
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

SECRET_KEY=$(< /dev/urandom tr -dc A-Z-a-z-0-9 | head -c64)

echo "Filling in Django settings..."

# Set up settings_local.py
sed -e "s|'ADMIN_NAME'|'$ADMIN_NAME'|g" \
	-e "s|'ADMIN_EMAIL'|'$ADMIN_EMAIL'|g" \
	-e "s|'DB_NAME'|'$DB_NAME'|g" \
	-e "s|'DB_USER'|'$DB_USER'|g" \
	-e "s|'DB_PASS'|'$DB_PASS'|g" \
	-e "s|'DB_HOST'|'$DB_HOST'|g" \
	-e "s|'DB_PORT'|'$DB_PORT'|g" \
	-e "s|'SRC_DIR'|'$SRC_DIR'|g" \
	-e "s|'DATA_DIR'|'$DATA_DIR'|g" \
	-e "s|'PROJECT_NAME'|'$PROJECT_NAME'|g" \
	-e "s|'SERVER_NAME'|'$SERVER_NAME'|g" \
	-e "s|'SERVER_IP'|'$SERVER_IP'|g" \
	-e "s|'TIME_ZONE'|'$TIME_ZONE'|g" \
	-e "s|'SECRET_KEY'|'$SECRET_KEY'|g" \
	$SRC_DIR/config/settings_local_template.py > \
	$SRC_DIR/config/settings_local.py

echo "$0: done"
