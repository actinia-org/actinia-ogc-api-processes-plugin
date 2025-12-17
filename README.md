# actinia-ogc-api-processes-plugin

This is a plugin for [actinia-core](https://github.com/mundialis/actinia_core) which adds OGC API Processes support and runs as standalone app.

## Installation & Setup
Use docker-compose for installation:
```bash
# -- plugin with actinia (& valkey)
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up

# -- only current plugin
docker compose -f docker/docker-compose.yml run --rm --service-ports --entrypoint sh actinia-ogc-api-processes
# within docker
gunicorn -b 0.0.0.0:3003 -w 8 --access-logfile=- -k gthread actinia_ogc_api_processes_plugin.main:flask_app
```

### DEV setup
```bash
# Uncomment the volume mount of the ogc-api-processes-plugin and additional marked sections of actinia-ogc-api-processes service within docker/docker-compose.yml,
# Note: might also need to set:
# - within config/mount/sample.ini: processing_base_url = http://127.0.0.1:8088/api/v3
# - within src/actinia_ogc_api_processes_plugin/main.py set port: flask_app.run(..., port=3003)
# then:
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up --build

# In another terminal: enter container, with stopping debugger:
docker attach $(docker ps | grep docker-actinia-ogc-api-processes | cut -d " " -f1)

# In another terminal: example call of processes-endpoint:
curl -u actinia-gdi:actinia-gdi -X GET http://localhost:3003/processes
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

### Running tests
**TODO: Add tests + update setup here**

You can run the tests in the actinia test docker:

```bash
docker build -f docker/actinia-ogc-api-processes-plugin-test/Dockerfile -t actinia-ogc-api-processes-plugin-test .
docker run -it actinia-ogc-api-processes-plugin-test -i

cd /src/actinia-ogc-api-processes-plugin/

# run all tests
make test

# run only unittests
make unittest
# run only integrationtests
make integrationtest

# run only tests which are marked for development with the decorator '@pytest.mark.dev'
make devtest
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
