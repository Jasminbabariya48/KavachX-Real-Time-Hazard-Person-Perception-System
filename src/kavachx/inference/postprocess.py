"""Image Preprocessing & Letterboxing Utilities."""
import cv2
import numpy as np
from typing import Tuple

def letterbox_with_meta(img: np.ndarray, new_shape: Tuple[int, int] = (640, 640), color: Tuple[int, int, int] = (114, 114, 114)):
    shape = img.shape[:2]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = (new_shape[1] - new_unpad[0]) / 2.0, (new_shape[0] - new_unpad[1]) / 2.0
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, dw, dh

def prepare_uint8_nchw(raw_bgr_frame: np.ndarray, target_shape=(640, 640)):
    frame_rgb = cv2.cvtColor(raw_bgr_frame, cv2.COLOR_BGR2RGB)
    lb, r, dw, dh = letterbox_with_meta(frame_rgb, target_shape)
    uint8_nchw = np.ascontiguousarray(np.transpose(lb, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)
    return uint8_nchw, r, dw, dh
