#!/bin/bash
#
# Fixes permissions for the project.  You may need to run this if you ran
# "./manage.py runserver" as the current user instead of $SERVER_USER.
#

DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh

# pass the username as the first argument (useful if using sudo)
LOCAL_USER=$USER
if [ $# -ge 1 ]; then
	LOCAL_USER=$1
fi

# Repository: owned by local user, viewable by webserver.
# (since the local user will be writing new files here).
chown -R $LOCAL_USER:$SERVER_GROUP $REPO_DIR/server
chmod u+r,g+r,o+r,u+w,g+w,u+X,g+X,o+X $REPO_DIR/server

# Run: only server has ownership
chown -R $SERVER_USER:$SERVER_GROUP $REPO_DIR/run
chmod u+r,g+r,o+r,u+w,g+w,u+X,g+X,o+X $REPO_DIR/run

# Data directories: owned by webserver, but editable by user.
# (since the webserver will be writing new files here).
chown -R $SERVER_USER:$LOCAL_USER $DATA_DIR
chmod u+r,g+r,o+r,u+w,g+w,u+X,g+X,o+X $DATA_DIR

# Backup: only local user has ownership
chown -R $LOCAL_USER:$LOCAL_USER $BACKUP_DIR
chmod u+r,g+r,o+r,u+w,g+w,u+X,g+X,o+X $BACKUP_DIR

# Data and backup: user and group have full edit permissions, no files are
# executable, and 'other' has read-only permissions.
bash -c "find $DATA_DIR $BACKUP_DIR -type d -exec chmod 775 {} \+"
bash -c "find $DATA_DIR $BACKUP_DIR -type f -exec chmod 664 {} \+"
