# SPDX-FileCopyrightText: (c) 2018-2025 by mundialis GmbH & Co. KG
# SPDX-License-Identifier: GPL-3.0-or-later

# Exception for hadolint-docker-linter:
# DL3007: using latest is prone to errors if the image will ever update. Pin the version explicitly to a release tag
# hadolint ignore=DL3007
FROM mundialis/actinia:latest

# pwgen is needed for the tests
RUN pip3 install --no-cache-dir pwgen==0.8.2.post0

COPY docker/actinia.cfg /etc/default/actinia
COPY src /src/actinia-ogc-api-processes-plugin/src/
COPY setup.cfg /src/actinia-ogc-api-processes-plugin/
COPY setup.py /src/actinia-ogc-api-processes-plugin/
COPY requirements.txt /src/actinia-ogc-api-processes-plugin/

RUN pip3 install --no-cache-dir -r /src/actinia-ogc-api-processes-plugin/requirements.txt && \
    pip3 uninstall actinia-ogc-api-processes-plugin.wsgi -y
# SETUPTOOLS_SCM_PRETEND_VERSION is only needed if in the plugin folder is no
# .git folder
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0

WORKDIR /src/actinia-ogc-api-processes-plugin
RUN pip3 install --no-cache-dir -e .

WORKDIR /src/actinia_core
