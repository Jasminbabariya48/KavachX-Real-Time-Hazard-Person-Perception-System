"""Health Check and Status Reporter."""
import os
import json

HEALTH_PATH = "/tmp/kawach_health.json"

def read_health_status() -> dict:
    if os.path.exists(HEALTH_PATH):
        try:
            with open(HEALTH_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"service": "kawach_worker", "state": "STOPPED"}

def is_worker_ready() -> bool:
    return read_health_status().get("state") == "READY"
