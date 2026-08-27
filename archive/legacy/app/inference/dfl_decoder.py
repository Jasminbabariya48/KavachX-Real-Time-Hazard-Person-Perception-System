"""Vectorized DFL Box & Class Decoder."""
import numpy as np

def decode_boxes_and_scores(tensor_7x8400, conf_threshold=0.25, class_names=None):
    if class_names is None:
        class_names = ["fire", "smoke", "person"]
    cx, cy, w, h = tensor_7x8400[0], tensor_7x8400[1], tensor_7x8400[2], tensor_7x8400[3]
    scores = tensor_7x8400[4:7]
    
    max_cls = np.argmax(scores, axis=0)
    max_scores = np.max(scores, axis=0)
    mask = max_scores >= conf_threshold
    
    candidates = []
    for idx in np.where(mask)[0]:
        c = int(max_cls[idx])
        s = float(max_scores[idx])
        candidates.append((c, s, cx[idx], cy[idx], w[idx], h[idx]))
    return candidates
