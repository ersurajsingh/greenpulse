#!/usr/bin/env python3
"""
GreenPulse Demo
Demonstrates idle → active → idle transition visible in Grafana.
Run alongside power_agent.py and data_processor.py.
"""

import time
import random

from greenpulse_sdk import Job

IDLE_SECS = 5
JOB_ID = "Performance_Test"


def dummy_workload(duration_secs: int = 10) -> float:
    """CPU-bound loop that runs for ~duration_secs seconds."""
    end = time.monotonic() + duration_secs
    result = 0.0
    while time.monotonic() < end:
        # Matrix-style dot product simulation without numpy dependency
        a = [random.random() for _ in range(500)]
        b = [random.random() for _ in range(500)]
        result += sum(x * y for x, y in zip(a, b))
    return result


def main():
    print("=" * 55)
    print("  GreenPulse Demo")
    print("=" * 55)

    # --- Idle phase ---
    print(f"\n[1/3] Idle phase ({IDLE_SECS}s) — job_id: system_idle")
    print("      Watch Grafana: power should be at baseline.")
    time.sleep(IDLE_SECS)

    # --- Active phase ---
    print(f"\n[2/3] Starting job '{JOB_ID}' — telemetry capture begins.")
    print("      Watch Grafana: power and CO2 should spike.")

    with Job(JOB_ID):
        print(f"      [JOB] Running heavy workload for ~10 seconds...")
        result = dummy_workload(duration_secs=10)
        print(f"      [JOB] Workload complete (checksum={result:.2f}).")
        print(f"      [JOB] Publishing stop signal and reverting to idle...")

    print(f"      Job '{JOB_ID}' finished — system reverted to system_idle.")

    # --- Post-idle phase ---
    print(f"\n[3/3] Post-job idle phase ({IDLE_SECS}s) — job_id: system_idle")
    print("      Watch Grafana: power should return to baseline.")
    time.sleep(IDLE_SECS)

    print("\n" + "=" * 55)
    print("  Demo complete. Check Grafana at http://localhost:3000")
    print("=" * 55)


if __name__ == "__main__":
    main()
