"""Event Manager and Alert Dispatcher."""
import time
from collections import deque
from typing import List
from app.inference.types import Detection
from .event_types import AlertEvent
from .alert_policy import SEVERITY_POLICY, EVENT_TYPE_MAP

class EventManager:
    def __init__(self, config: dict):
        self.config = config
        self.cooldown_sec = config.get("cooldown_seconds", 3.0)
        self.last_dispatched = {}
        self.recent_events = deque(maxlen=100)

    def process_detections(self, detections: List[Detection], frame=None) -> List[AlertEvent]:
        now = time.time()
        dispatched = []
        for det in detections:
            cname = det.class_name
            if cname in self.last_dispatched:
                if now - self.last_dispatched[cname] < self.cooldown_sec:
                    continue
            self.last_dispatched[cname] = now
            event = AlertEvent(
                event_type=EVENT_TYPE_MAP.get(cname, "HAZARD_DETECTED"),
                class_name=cname,
                severity=SEVERITY_POLICY.get(cname, "WARNING"),
                confidence=det.confidence,
                bbox=det.bbox,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            )
            dispatched.append(event)
            self.recent_events.append(event)
        return dispatched
