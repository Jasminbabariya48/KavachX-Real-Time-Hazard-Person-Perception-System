"""Post-processing and Coordinate Un-letterboxing."""
import numpy as np
from .types import Detection
from .dfl_decoder import decode_boxes_and_scores

def decode_and_filter_detections(tensor_7x8400, r, dw, dh, conf_threshold=0.25, class_names=None):
    if class_names is None:
        class_names = ["fire", "smoke", "person"]
    candidates = decode_boxes_and_scores(tensor_7x8400, conf_threshold, class_names)
    
    detections = []
    for c, s, cx, cy, w, h in candidates:
        bx1 = (cx - w / 2.0 - dw) / r
        by1 = (cy - h / 2.0 - dh) / r
        bx2 = (cx + w / 2.0 - dw) / r
        by2 = (cy + h / 2.0 - dh) / r
        
        detections.append(Detection(
            class_id=c,
            class_name=class_names[c],
            confidence=round(float(s), 3),
            bbox=[round(float(v), 1) for v in [bx1, by1, bx2, by2]]
        ))
    return detections
