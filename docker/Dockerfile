# SPDX-FileCopyrightText: (c) 2018-2025 by mundialis GmbH & Co. KG
# SPDX-License-Identifier: GPL-3.0-or-later

FROM alpine:3.23

# python3 + pip3
# hadolint ignore=DL3018
RUN apk update; \
    apk add --no-cache python3 python3-dev make
ENV PATH="/opt/venv/bin:$PATH"
RUN /usr/bin/python -m venv --system-site-packages --without-pip /opt/venv
# hadolint ignore=DL3013
RUN python -m ensurepip && pip3 install --no-cache-dir --upgrade pip pep517 wheel

# hadolint ignore=DL3013
RUN pip3 install --no-cache-dir gunicorn && \
    # needed for tests
    pip3 install --no-cache-dir setuptools pwgen==0.8.2.post0 pytest==8.3.5 pytest-cov==6.0.0

COPY . /src/actinia-ogc-api-processes-plugin/
RUN pip3 install --no-cache-dir -e /src/actinia-ogc-api-processes-plugin/

WORKDIR /src/actinia-ogc-api-processes-plugin
# RUN make test

CMD ["gunicorn", "-b", "0.0.0.0:4044", "-w", "8", "--access-logfile=-", "-k", "gthread", "actinia_ogc_api_processes_plugin.main:flask_app"]
