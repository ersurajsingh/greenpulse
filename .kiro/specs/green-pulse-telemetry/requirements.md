# Requirements Document

## Introduction

GreenPulse is a local, low-profile proof-of-concept telemetry tool for monitoring AI workload energy and resource consumption. The system runs entirely via Docker Compose and wires together three services: an MQTT broker for telemetry ingestion, a time-series database for storage, and a dashboarding tool for visualization. All data is persisted to local volumes so state survives container restarts.

## Glossary

- **GreenPulse**: The overall telemetry POC system described in this document.
- **MQTT_Broker**: The Eclipse Mosquitto service that receives telemetry messages over MQTT.
- **InfluxDB**: The InfluxDB 2.x time-series database service used to store telemetry data.
- **Grafana**: The Grafana visualization service used to display telemetry dashboards.
- **Docker_Compose**: The container orchestration tool used to define and run all services.
- **Volume**: A Docker-managed persistent storage mount that survives container restarts.
- **Org**: The InfluxDB organization namespace, set to "GreenPulse".
- **Bucket**: The InfluxDB data bucket used for telemetry, named "telemetry".
- **Dev_Token**: A static API token used for development-time authentication with InfluxDB.

---

## Requirements

### Requirement 1: MQTT Broker Service

**User Story:** As a developer, I want an MQTT broker running locally, so that telemetry producers can publish messages to a well-known endpoint.

#### Acceptance Criteria

1. THE Docker_Compose SHALL define a service running Eclipse Mosquitto on port 1883.
2. WHEN the Mosquitto container starts, THE MQTT_Broker SHALL accept connections on TCP port 1883.
3. THE Docker_Compose SHALL mount a named Volume to persist Mosquitto data and configuration across container restarts.
4. IF the Mosquitto container is stopped and restarted, THEN THE MQTT_Broker SHALL retain its configuration without requiring manual re-setup.

---

### Requirement 2: InfluxDB Time-Series Storage Service

**User Story:** As a developer, I want InfluxDB 2.x running locally, so that telemetry data can be stored and queried as time-series records.

#### Acceptance Criteria

1. THE Docker_Compose SHALL define a service running InfluxDB 2.x on port 8086.
2. WHEN the InfluxDB container starts, THE InfluxDB SHALL be pre-configured with the Org value "GreenPulse".
3. WHEN the InfluxDB container starts, THE InfluxDB SHALL be pre-configured with the Bucket named "telemetry".
4. WHEN the InfluxDB container starts, THE InfluxDB SHALL be pre-configured with a static Dev_Token for API authentication.
5. THE Docker_Compose SHALL mount a named Volume to persist InfluxDB data across container restarts.
6. IF the InfluxDB container is stopped and restarted, THEN THE InfluxDB SHALL retain all previously written telemetry data.

---

### Requirement 3: Grafana Visualization Service

**User Story:** As a developer, I want Grafana running locally, so that I can visualize telemetry data through dashboards.

#### Acceptance Criteria

1. THE Docker_Compose SHALL define a service running Grafana on port 3000.
2. WHEN the Grafana container starts, THE Grafana SHALL be accessible via a web browser at http://localhost:3000.
3. THE Docker_Compose SHALL mount a named Volume to persist Grafana dashboard configurations and data sources across container restarts.
4. IF the Grafana container is stopped and restarted, THEN THE Grafana SHALL retain any previously configured dashboards and data sources.

---

### Requirement 4: Persistent Volume Configuration

**User Story:** As a developer, I want all service data persisted to local Docker volumes, so that I do not lose telemetry data or configuration when containers are stopped.

#### Acceptance Criteria

1. THE Docker_Compose SHALL declare named volumes for each service (MQTT_Broker, InfluxDB, and Grafana).
2. WHEN any container is stopped and restarted using `docker compose up`, THE Docker_Compose SHALL remount the same named volumes so that no data is lost.
3. THE Docker_Compose SHALL use Docker-managed named volumes rather than bind mounts, so that volume lifecycle is managed by Docker.

---

### Requirement 5: Service Composition and Startup

**User Story:** As a developer, I want all three services to start with a single command, so that I can spin up the full GreenPulse stack quickly.

#### Acceptance Criteria

1. THE Docker_Compose SHALL define all three services (MQTT_Broker, InfluxDB, Grafana) in a single `docker-compose.yml` file.
2. WHEN `docker compose up` is executed, THE Docker_Compose SHALL start all three services concurrently.
3. THE Docker_Compose SHALL use specific, pinned image versions for each service to ensure reproducible builds.
4. WHEN any service fails to start, THE Docker_Compose SHALL surface the failure in container logs without silently ignoring it.
