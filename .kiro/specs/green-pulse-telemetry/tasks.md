# Implementation Plan: GreenPulse Telemetry POC

## Overview

Implement the GreenPulse local telemetry stack by creating a `docker-compose.yml` file, a Mosquitto configuration file, and a structural test suite that validates the compose file against the correctness properties in the design document.

## Tasks

- [x] 1. Create Mosquitto configuration file
  - Create `mosquitto/config/mosquitto.conf` with anonymous listener on port 1883 and persistence enabled
  - This file will be bind-mounted into the Mosquitto container at `/mosquitto/config/mosquitto.conf`
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Create the docker-compose.yml file
  - [x] 2.1 Define the Mosquitto service
    - Use image `eclipse-mosquitto:2.0`
    - Map host port 1883 to container port 1883
    - Mount `mosquitto_data` named volume to `/mosquitto/data`
    - Mount the `mosquitto/config/mosquitto.conf` config file into the container
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Define the InfluxDB service
    - Use image `influxdb:2.7`
    - Map host port 8086 to container port 8086
    - Set all five initialization env vars: `DOCKER_INFLUXDB_INIT_MODE=setup`, `DOCKER_INFLUXDB_INIT_ORG=GreenPulse`, `DOCKER_INFLUXDB_INIT_BUCKET=telemetry`, `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=greenpulse-dev-token`, `DOCKER_INFLUXDB_INIT_USERNAME=admin`, `DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword`
    - Mount `influxdb_data` named volume to `/var/lib/influxdb2`
    - Mount `influxdb_config` named volume to `/etc/influxdb2`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 2.3 Define the Grafana service
    - Use image `grafana/grafana:10.4.2`
    - Map host port 3000 to container port 3000
    - Mount `grafana_data` named volume to `/var/lib/grafana`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.4 Declare all named volumes at the top level
    - Declare `mosquitto_data`, `influxdb_data`, `influxdb_config`, `grafana_data` in the top-level `volumes` section
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Write structural tests for the docker-compose.yml
  - [x] 3.1 Set up test file and YAML parsing fixture
    - Create `tests/test_compose.py`
    - Add a pytest fixture that parses `docker-compose.yml` using PyYAML and returns the dict
    - _Requirements: 5.1_

  - [x]* 3.2 Write structural test for Property 1 (services and ports)
    - Assert that `mosquitto`, `influxdb`, and `grafana` services exist
    - Assert each service exposes the correct host port (1883, 8086, 3000)
    - **Property 1: All services are declared with correct ports**
    - **Validates: Requirements 1.1, 2.1, 3.1, 5.1**

  - [x]* 3.3 Write structural test for Property 2 (pinned image versions)
    - For each service in the compose file, assert the image tag is present and is not `latest`
    - **Property 2: All service images are pinned to specific versions**
    - **Validates: Requirements 5.3**

  - [x]* 3.4 Write structural test for Property 3 (named volumes, no bind mounts)
    - For each service, assert at least one named volume is mounted
    - Assert no volume mount value starts with `./` or `/` (no bind mounts for persistence)
    - Assert all mounted volume names appear in the top-level `volumes` section
    - **Property 3: Named volumes are declared and mounted for every service**
    - **Validates: Requirements 1.3, 2.5, 3.3, 4.1, 4.3**

  - [x]* 3.5 Write structural test for Property 4 (InfluxDB env vars present and non-empty)
    - Assert all five required `DOCKER_INFLUXDB_INIT_*` env vars are defined in the influxdb service
    - Assert none of them are empty strings
    - **Property 4: InfluxDB initialization environment variables are all present and non-empty**
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [x]* 3.6 Write structural test for Property 5 (InfluxDB org and bucket values)
    - Assert `DOCKER_INFLUXDB_INIT_ORG` equals `"GreenPulse"`
    - Assert `DOCKER_INFLUXDB_INIT_BUCKET` equals `"telemetry"`
    - **Property 5: InfluxDB org and bucket values match specification**
    - **Validates: Requirements 2.2, 2.3**

- [x] 4. Checkpoint — Ensure all structural tests pass
  - Run `pytest tests/test_compose.py -v` and confirm all tests pass. Ask the user if any questions arise.

- [ ]* 5. Write integration smoke tests (optional)
  - [ ]* 5.1 Write TCP connectivity test for Mosquitto
    - Use `socket` to attempt a TCP connection to `localhost:1883` after stack is up
    - _Requirements: 1.2_

  - [ ]* 5.2 Write HTTP health check test for InfluxDB
    - Use `requests` to GET `http://localhost:8086/health` and assert HTTP 200
    - _Requirements: 2.1_

  - [ ]* 5.3 Write HTTP health check test for Grafana
    - Use `requests` to GET `http://localhost:3000` and assert HTTP 200
    - _Requirements: 3.2_

- [x] 6. Final checkpoint — Verify the full stack starts cleanly
  - Ensure all structural tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Run the stack with: `docker compose up -d`
- Stop the stack with: `docker compose down` (add `-v` only if you want to wipe volumes)
- Structural tests require only `pytest` and `PyYAML` — no running Docker daemon needed
- Integration tests (task 5) require the stack to be running before executing
