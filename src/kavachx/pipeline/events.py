"""Hazard and Person Event Manager."""
import time
from collections import deque
from typing import List
from kavachx.inference.model import Detection

class AlertEventManager:
    def __init__(self, config: dict):
        self.cooldown_sec = config.get("cooldown_seconds", 3.0)
        self.last_dispatched = {}
        self.recent_events = deque(maxlen=100)

    def process(self, detections: List[Detection]) -> List[dict]:
        now = time.time()
        dispatched = []
        for det in detections:
            cname = det.class_name
            if cname in self.last_dispatched:
                if now - self.last_dispatched[cname] < self.cooldown_sec:
                    continue
            self.last_dispatched[cname] = now
            ev = {
                "event_type": "HAZARD_DETECTED" if cname in ["fire", "smoke"] else "PERSON_DETECTED",
                "class_name": cname,
                "severity": "CRITICAL" if cname == "fire" else "WARNING",
                "confidence": det.confidence,
                "bbox": det.bbox,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            }
            dispatched.append(ev)
            self.recent_events.append(ev)
        return dispatched
