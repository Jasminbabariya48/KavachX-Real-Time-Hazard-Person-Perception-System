"""Image Preprocessing and Letterboxing."""
import cv2
import numpy as np

def letterbox_with_meta(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw, dh = dw / 2.0, dh / 2.0
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, dw, dh

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    lb, _, _, _ = letterbox_with_meta(img, new_shape, color)
    return lb

def prepare_uint8_nchw(raw_bgr_frame, target_shape=(640, 640)):
    frame_rgb = cv2.cvtColor(raw_bgr_frame, cv2.COLOR_BGR2RGB)
    lb, r, dw, dh = letterbox_with_meta(frame_rgb, target_shape)
    uint8_nchw = np.ascontiguousarray(np.transpose(lb, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)
    return uint8_nchw, r, dw, dh
