"""Event and Alert Data Types."""
from dataclasses import dataclass
from typing import List

@dataclass
class AlertEvent:
    event_type: str # HAZARD_DETECTED | PERSON_DETECTED
    class_name: str
    severity: str   # CRITICAL | WARNING | INFO
    confidence: float
    bbox: List[float]
    timestamp: str
