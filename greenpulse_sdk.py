"""
GreenPulse SDK
Provides the Job context manager for tracking named workloads via MQTT.
"""

import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
CONTROL_TOPIC = "greenpulse/control"
IDLE_JOB_ID = "system_idle"


class Job:
    """Context manager that signals job start/stop to the GreenPulse control topic.

    Usage:
        with Job("model_training"):
            train(...)
    """

    def __init__(
        self,
        job_id: str,
        broker: str = MQTT_BROKER,
        port: int = MQTT_PORT,
    ) -> None:
        self.job_id = job_id
        self.broker = broker
        self.port = port
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def _publish(self, action: str, job_id: str) -> None:
        payload = json.dumps({
            "action": action,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._client.publish(CONTROL_TOPIC, payload, qos=1)

    def __enter__(self) -> "Job":
        self._client.connect(self.broker, self.port, keepalive=60)
        self._client.loop_start()
        self._publish("start", self.job_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._publish("stop", self.job_id)
        self._publish("start", IDLE_JOB_ID)  # revert to idle
        self._client.loop_stop()
        self._client.disconnect()
        return False  # don't suppress exceptions
