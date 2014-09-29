FROM ubuntu
MAINTAINER Martin Kiefel "mk@nopw.de"

ENV LC_ALL C.UTF-8

# create container user
RUN useradd --create-home appuser

ENV REPO_DIR /home/appuser
RUN mkdir -p "${REPO_DIR}/scripts/install"

COPY scripts/config.sh /home/appuser/scripts/config.sh
COPY scripts/load_config.sh /home/appuser/scripts/load_config.sh

# install system packages
COPY scripts/install/install_packages.sh /home/appuser/scripts/install/install_packages.sh
COPY scripts/install/requirements-packages.txt /home/appuser/scripts/install/requirements-packages.txt
RUN "${REPO_DIR}/scripts/install/install_packages.sh"

# install nodejs packages
COPY scripts/install/install_nodejs.sh /home/appuser/scripts/install/install_nodejs.sh
RUN "${REPO_DIR}/scripts/install/install_nodejs.sh"

# install python packages
COPY scripts/install/install_python.sh /home/appuser/scripts/install/install_python.sh
COPY scripts/install/requirements-python-0.txt /home/appuser/scripts/install/requirements-python-0.txt
COPY scripts/install/requirements-python-1.txt /home/appuser/scripts/install/requirements-python-1.txt
RUN "${REPO_DIR}/scripts/install/install_python.sh"

# configure memcached
COPY scripts/install/install_memcached.sh /home/appuser/scripts/install/install_memcached.sh
RUN "${REPO_DIR}/scripts/install/install_memcached.sh"

COPY server /home/appuser/server

# create and fix dirs
COPY scripts/install/install_dirs.sh /home/appuser/scripts/install/install_dirs.sh
COPY scripts/fix_permissions.sh /home/appuser/scripts/fix_permissions.sh
RUN "${REPO_DIR}/scripts/install/install_dirs.sh"

# configure nginx
COPY scripts/install/install_nginx.sh /home/appuser/scripts/install/install_nginx.sh
COPY scripts/make_public.sh /home/appuser/scripts/make_public.sh
COPY scripts/collect_static.sh /home/appuser/scripts/collect_static.sh
RUN "${REPO_DIR}/scripts/install/install_nginx.sh"

# configure django
COPY scripts/install/install_server.sh /home/appuser/scripts/install/install_server.sh
RUN "${REPO_DIR}/scripts/install/install_server.sh"

# copy the rest of the scripts
COPY scripts /home/appuser/scripts

EXPOSE 80
