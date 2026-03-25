#!/usr/bin/env python3
"""
GreenPulse Data Processor
Subscribes to MQTT power/control topics, enriches with CO2 intensity,
and writes to InfluxDB 2.x.
"""

import json
import signal
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- MQTT config ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_POWER = "greenpulse/hardware/power"
TOPIC_CONTROL = "greenpulse/control"

# --- InfluxDB config ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "greenpulse-dev-token"
INFLUX_ORG = "GreenPulse"
INFLUX_BUCKET = "telemetry"

# --- Carbon intensity: kg CO2 per kWh (standard grid average) ---
CARBON_INTENSITY_KG_PER_KWH = 0.475

# --- Global state ---
current_job_id = "system_idle"


def watts_to_co2_grams(power_w: float) -> float:
    """Convert instantaneous Watts to CO2 grams for a 1-second sample.

    Formula: (W / 1000) * (1/3600) hours * intensity_kg_per_kWh * 1000 g/kg
    Simplified: power_w * intensity / 3600
    """
    return round(power_w * CARBON_INTENSITY_KG_PER_KWH / 3600, 6)


def make_influx_client():
    return InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)


def on_message(client, userdata, msg):
    global current_job_id

    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[WARN] Could not parse message on {msg.topic}: {e}")
        return

    if msg.topic == TOPIC_CONTROL:
        action = payload.get("action")
        job_id = payload.get("job_id", "system_idle")
        if action == "start":
            current_job_id = job_id
            print(f"[CONTROL] Job started: {current_job_id}")
        elif action == "stop":
            print(f"[CONTROL] Job stopped: {current_job_id}")
            current_job_id = "system_idle"

    elif msg.topic == TOPIC_POWER:
        cpu_w = float(payload.get("cpu_w", 0.0))
        gpu_w = float(payload.get("gpu_w", 0.0))
        total_w = cpu_w + gpu_w
        co2_g = watts_to_co2_grams(total_w)
        ts = payload.get("timestamp", datetime.now(timezone.utc).isoformat())

        point = (
            Point("power_reading")
            .tag("job_id", current_job_id)
            .field("power_w", total_w)
            .field("cpu_w", cpu_w)
            .field("gpu_w", gpu_w)
            .field("co2_g", co2_g)
            .time(ts, WritePrecision.NANOSECONDS)
        )

        write_api = userdata["write_api"]
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(f"[POWER] job={current_job_id}  total={total_w}W  co2={co2_g}g")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(TOPIC_POWER, qos=1)
        client.subscribe(TOPIC_CONTROL, qos=1)
        print(f"Subscribed to: {TOPIC_POWER}, {TOPIC_CONTROL}")
    else:
        print(f"[ERROR] MQTT connection failed: {reason_code}")
        sys.exit(1)


def run():
    influx_client = make_influx_client()
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        userdata={"write_api": write_api},
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    def _shutdown(sig, frame):
        print("\nShutting down...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        influx_client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("GreenPulse data processor running. Press Ctrl+C to stop.")
    mqtt_client.loop_forever()


if __name__ == "__main__":
    run()
