"""DFL Box Decoder & Postprocessor."""
import numpy as np
from typing import List
from .model import Detection

def decode_detections(tensor_7x8400: np.ndarray, r: float, dw: float, dh: float, conf_thresh: float = 0.25, class_names: List[str] = None) -> List[Detection]:
    if class_names is None:
        class_names = ["fire", "smoke", "person"]
    cx, cy, w, h = tensor_7x8400[0], tensor_7x8400[1], tensor_7x8400[2], tensor_7x8400[3]
    scores = tensor_7x8400[4:7]
    
    max_cls = np.argmax(scores, axis=0)
    max_scores = np.max(scores, axis=0)
    mask = max_scores >= conf_thresh
    
    detections = []
    for idx in np.where(mask)[0]:
        c = int(max_cls[idx])
        s = float(max_scores[idx])
        bx1 = (cx[idx] - w[idx] / 2.0 - dw) / r
        by1 = (cy[idx] - h[idx] / 2.0 - dh) / r
        bx2 = (cx[idx] + w[idx] / 2.0 - dw) / r
        by2 = (cy[idx] + h[idx] / 2.0 - dh) / r
        
        detections.append(Detection(
            class_id=c,
            class_name=class_names[c],
            confidence=round(float(s), 3),
            bbox=[round(float(v), 1) for v in [bx1, by1, bx2, by2]]
        ))
    return detections
