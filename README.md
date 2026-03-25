# GreenPulse 🌱

A local, low-profile proof-of-concept telemetry tool for monitoring AI workload energy consumption and carbon footprint in real time.

## Architecture

```
Telemetry Producer (power_agent.py)
        │
        │ MQTT  greenpulse/hardware/power
        ▼
Eclipse Mosquitto (broker :1883)
        │
        ▼
data_processor.py  ──────────────────► InfluxDB 2.x (:8086)
        ▲                                      │
        │ MQTT  greenpulse/control             ▼
greenpulse_sdk.py (Job context manager)   Grafana (:3000)
```

## Stack

| Service | Image | Port |
|---|---|---|
| Eclipse Mosquitto | `eclipse-mosquitto:2.0` | 1883 |
| InfluxDB 2.x | `influxdb:2.7` | 8086 |
| Grafana | `grafana/grafana:10.4.2` | 3000 |

## Prerequisites

- Docker + Docker Compose
- Python 3.9+

```bash
pip install psutil paho-mqtt influxdb-client
```

Optional (NVIDIA GPU support):
```bash
pip install pynvml
```

## Quick Start

**1. Start the infrastructure**
```bash
docker compose up -d
```

**2. Start the data processor** (subscribes MQTT → writes InfluxDB)
```bash
python data_processor.py
```

**3. Start the power agent** (publishes readings every second)
```bash
python power_agent.py
```

**4. Run the demo**
```bash
python demo.py
```

## Files

| File | Description |
|---|---|
| `docker-compose.yml` | Full infrastructure stack |
| `mosquitto/config/mosquitto.conf` | Mosquitto broker config |
| `power_agent.py` | Collects CPU/GPU power, publishes to MQTT |
| `data_processor.py` | Enriches power data with CO2, writes to InfluxDB |
| `greenpulse_sdk.py` | `Job` context manager for tagging workloads |
| `demo.py` | Demo script showing idle → active → idle transition |
| `tests/test_compose.py` | Structural tests for docker-compose.yml |

## SDK Usage

Tag any Python workload to track its energy footprint:

```python
from greenpulse_sdk import Job

with Job("model_training"):
    train_model()
```

This publishes `start`/`stop` control messages so `data_processor.py` tags all power readings during the block with `job_id=model_training`.

## Grafana Setup

1. Open [http://localhost:3000](http://localhost:3000) (default: `admin` / `admin`)
2. Add InfluxDB data source:
   - URL: `http://influxdb:8086`
   - Token: `greenpulse-dev-token`
   - Org: `GreenPulse`
   - Bucket: `telemetry`
3. Query the `power_reading` measurement for `power_w`, `co2_g`, filtered by `job_id`

## Power Model

| Component | Formula |
|---|---|
| CPU | `50W idle + (cpu_utilization% × 2W)` |
| GPU | `20W idle + (gpu_utilization% × 2.5W)` (mock if no NVIDIA GPU) |
| CO2 | `total_watts × 0.475 kg/kWh ÷ 3600` per second |

Carbon intensity factor: **0.475 kg CO2/kWh** (standard grid average)

## Stopping the Stack

```bash
docker compose down        # stop containers, keep volumes
docker compose down -v     # stop containers AND wipe all data
```
