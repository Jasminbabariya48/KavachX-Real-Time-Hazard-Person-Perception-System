"""Service Health Inspection."""
import os
import json

HEALTH_FILE = "/tmp/kawach_health.json"

def get_service_health() -> dict:
    if os.path.exists(HEALTH_FILE):
        try:
            with open(HEALTH_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"service": "kawach_worker", "state": "STOPPED"}

def is_healthy() -> bool:
    return get_service_health().get("state") == "READY"
