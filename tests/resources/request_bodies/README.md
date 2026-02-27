# Example request bodies

Basic settings:

```bash
AUTH="actinia-gdi:actinia-gdi"
BASEURL="http://localhost:4044"
```

Raster neighbor hood example with `r.neighbors`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_r_neighbors.json ${BASEURL}/processes/r.neighbors/execution
```

Vector buffer example with `v.buffer`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_v_buffer.json ${BASEURL}/processes/v.buffer/execution
```

Vector export example with `point_in_polygon`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_point_in_polygon.json ${BASEURL}/processes/point_in_polygon/execution
```

Generates slope and aspect of elevation map with `slope_aspect`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_slope_aspect.json ${BASEURL}/processes/slope_aspect/execution
```

Example actinia-module to create and export a STRDS with `strds_create_and_export`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_strds_create_and_export.json ${BASEURL}/processes/strds_create_and_export/execution
```

Extracts all hospitals in one county and export the resulting vector; additional process_results is a stdout-json with adresses with `get_county_hospitals`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_get_county_hospitals.json ${BASEURL}/processes/get_county_hospitals/execution
```

Simulation of a classification error matrix as example for text file export with `classification_error_matrix`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_classification_error_matrix.json ${BASEURL}/processes/classification_error_matrix/execution
```

Example actinia-module for stdout with `elevation_stdout`:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_elevation_stdout.json ${BASEURL}/processes/elevation_stdout/execution
```

Example point buffering with **input by reference**:

```bash
curl -X POST \
    -H 'Content-Type: application/json' -H 'accept: application/json' \
    -u ${AUTH} \
    -d @test_v_buffer_by_reference.json ${BASEURL}/processes/v.buffer/execution
```
