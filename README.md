# actinia-ogc-api-processes-plugin

This is a plugin for [actinia-core](https://github.com/mundialis/actinia_core) which adds OGC API Processes support and runs as standalone app.

## Installation & Setup
Use docker-compose for installation:
```bash
# -- plugin with actinia (& valkey)
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up

# -- only current plugin (Note: need to start actinia + valkey separately)
docker compose -f docker/docker-compose.yml run --rm --service-ports --entrypoint sh actinia-ogc-api-processes
# within docker
gunicorn -b 0.0.0.0:4044 -w 8 --access-logfile=- -k gthread actinia_ogc_api_processes_plugin.main:flask_app
```

### DEV setup
```bash
# Uncomment the volume mount of the ogc-api-processes-plugin and additional marked sections of actinia-ogc-api-processes service within docker/docker-compose.yml,
# Note: might also need to set:
# - within config/mount/sample.ini: processing_base_url = http://127.0.0.1:8088/api/v3
# - within src/actinia_ogc_api_processes_plugin/main.py set port: flask_app.run(..., port=4044)
# then:
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up --build

# In another terminal: enter container, with stopping debugger:
docker attach $(docker ps | grep docker-actinia-ogc-api-processes | cut -d " " -f1)

# In another terminal: example call of processes-endpoint:
curl -u actinia-gdi:actinia-gdi -X GET http://localhost:4044/processes
```

### Installation hints
* If you get an error like: `ERROR: for docker_kvdb_1  Cannot start service valkey: network xxx not found` you can try the following:
```bash
docker compose -f docker/docker-compose.yml down
# remove all custom networks not used by a container
docker network prune
docker compose -f docker/docker-compose.yml up -d
```

### Hints

* If you have no `.git` folder in the plugin folder, you need to set the
`SETUPTOOLS_SCM_PRETEND_VERSION` before installing the plugin:
```bash
export SETUPTOOLS_SCM_PRETEND_VERSION=0.0
```
Otherwise you will get an error like this
`LookupError: setuptools-scm was unable to detect version for '/src/actinia-ogc-api-processes-plugin'.`.

* If you make changes in code and nothing changes you can try to uninstall the plugin:
```bash
pip3 uninstall actinia-ogc-api-processes-plugin.wsgi -y
rm -rf /usr/lib/python3.8/site-packages/actinia_ogc_api_processes_plugin.wsgi-*.egg
```

## Running tests

You can run the tests with following setup:

```bash
# First: Uncomment the volume mount of the ogc-api-processes-plugin of actinia-ogc-api-processes service within docker/docker-compose.yml
# Then start containers for testing
docker compose -f "docker/docker-compose.yml" up -d --build


# run all tests
docker exec -t docker-actinia-ogc-api-processes-1 make test

# run only unittests
docker exec -t docker-actinia-ogc-api-processes-1 make unittest

# run only integrationtests
docker exec -t docker-actinia-ogc-api-processes-1 make integrationtest

# run only tests which are marked for development with the decorator '@pytest.mark.dev'
docker exec -t docker-actinia-ogc-api-processes-1 make devtest


# Stop containers after finishing testing
docker compose -f "docker/docker-compose.yml" down
```

## Hint for the development of actinia plugins

### skip permission check
The parameter [`skip_permission_check`](https://github.com/actinia-org/actinia-processing-lib/blob/1.1.1/src/actinia_processing_lib/ephemeral_processing.py#L1914-L1917) (see [example in actinia-statistic plugin](https://github.com/actinia-org/actinia-statistic-plugin/blob/0.3.1/src/actinia_statistic_plugin/vector_sampling.py#L224))
should only be set to `True` if you are sure that you really don't want to check the permissions.

The skip of the permission check leads to a skipping of:
* [the module check](https://github.com/actinia-org/actinia-processing-lib/blob/1.1.1/src/actinia_processing_lib/ephemeral_processing.py#L676-L688)
* [the limit of the number of processes](https://github.com/actinia-org/actinia-processing-lib/blob/1.1.1/src/actinia_processing_lib/ephemeral_processing.py#L658-L667)
* the limit of the processing time

Not skipped are:
* the limit of the cells
* the mapset/project limitations of the user
