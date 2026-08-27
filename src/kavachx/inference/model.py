"""Inference Data Models."""
from dataclasses import dataclass
from typing import List

@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float] # [x1, y1, x2, y2] unletterboxed coordinates

@dataclass
class InferenceOutput:
    status: int
    request_id: int
    infer_time_ms: float
    postproc_time_ms: float
    roundtrip_time_ms: float
    detections: List[Detection]
