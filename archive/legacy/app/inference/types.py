"""Inference Data Types and Detection Schema."""
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float] # [x1, y1, x2, y2] unpadded original coords

@dataclass
class InferenceResult:
    status: int
    request_id: int
    inference_time_ms: float
    postprocess_time_ms: float
    roundtrip_time_ms: float
    detections: List[Detection]
