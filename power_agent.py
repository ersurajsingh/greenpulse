#!/usr/bin/env python3
"""
GreenPulse Power Agent
Collects CPU/GPU power telemetry and publishes to MQTT every second.
"""

import json
import time
import argparse
from datetime import datetime, timezone

import psutil
import paho.mqtt.client as mqtt

# --- GPU support (optional) ---
try:
    import pynvml
    pynvml.nvmlInit()
    _NVML_AVAILABLE = True
except Exception:
    _NVML_AVAILABLE = False

# --- Power model constants ---
CPU_IDLE_W = 50.0       # baseline idle watts
CPU_SCALE_W = 2.0       # additional watts per % utilization (0-100)
GPU_IDLE_W = 20.0       # mock GPU idle watts
GPU_SCALE_W = 2.5       # mock GPU watts per % utilization

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "greenpulse/hardware/power"


def get_cpu_power() -> float:
    """Return estimated CPU power draw in Watts."""
    utilization = psutil.cpu_percent(interval=None)  # non-blocking; caller must prime first
    return round(CPU_IDLE_W + utilization * CPU_SCALE_W, 2)


def get_gpu_power() -> float:
    """Return GPU power draw in Watts (real via pynvml, or mocked)."""
    if _NVML_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            milliwatts = pynvml.nvmlDeviceGetPowerUsage(handle)
            return round(milliwatts / 1000.0, 2)
        except Exception:
            pass
    # Mock: simulate a GPU at ~30% utilization
    mock_utilization = 30.0
    return round(GPU_IDLE_W + mock_utilization * GPU_SCALE_W, 2)


def build_payload(job_id: str) -> str:
    """Build and return the JSON telemetry payload."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_w": get_cpu_power(),
        "gpu_w": get_gpu_power(),
        "job_id": job_id,
    }
    return json.dumps(payload)


def run(job_id: str, broker: str, port: int, interval: float) -> None:
    """Connect to MQTT broker and publish telemetry in a loop."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"Connected to MQTT broker at {broker}:{port}")
        else:
            print(f"Connection failed with code {reason_code}")

    client.on_connect = on_connect
    client.connect(broker, port, keepalive=60)
    client.loop_start()

    # Prime psutil so the first reading isn't 0.0
    psutil.cpu_percent(interval=None)
    time.sleep(0.1)

    print(f"Publishing to '{MQTT_TOPIC}' every {interval}s  (job_id={job_id})")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            payload = build_payload(job_id)
            client.publish(MQTT_TOPIC, payload, qos=1)
            print(payload)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GreenPulse power telemetry agent")
    parser.add_argument("--job-id", default="system_idle", help="Job identifier tag")
    parser.add_argument("--broker", default=MQTT_BROKER, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=MQTT_PORT, help="MQTT broker port")
    parser.add_argument("--interval", type=float, default=1.0, help="Publish interval in seconds")
    args = parser.parse_args()

    run(args.job_id, args.broker, args.port, args.interval)
