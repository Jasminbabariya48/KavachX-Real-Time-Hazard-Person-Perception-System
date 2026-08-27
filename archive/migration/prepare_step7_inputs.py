import cv2
import numpy as np
import onnxruntime as ort
import json
import os

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2] # [height, width]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img

def prepare():
    os.makedirs('/home/work_user2/kawachx_task/results/step7_htp_execution/inputs', exist_ok=True)
    os.makedirs('/home/work_user2/kawachx_task/results/step7_htp_execution/fp32_reference', exist_ok=True)

    samples = [
        ('fire', '/home/work_user2/kawachx_task/test_images/fire.jpg'),
        ('fire_2', '/home/work_user2/kawachx_task/test_images/fire_2.jpg'),
        ('person', '/home/work_user2/kawachx_task/test_images/person.jpg')
    ]

    # FP32 ONNX session
    onnx_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx'
    split_onnx_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32_htp_split.onnx'
    sess_split = ort.InferenceSession(split_onnx_path, providers=['CPUExecutionProvider'])
    sess_orig  = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])

    for name, img_path in samples:
        img = cv2.imread(img_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        lb_img = letterbox(img_rgb, (640, 640))

        # UINT8 NCHW
        uint8_nchw = np.ascontiguousarray(np.transpose(lb_img, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)
        uint8_path = f"/home/work_user2/kawachx_task/results/step7_htp_execution/inputs/{name}_uint8.raw"
        uint8_nchw.tofile(uint8_path)
        print(f"Saved {uint8_path} ({uint8_nchw.nbytes} bytes)")

        # FP32 NCHW [0.0, 1.0]
        fp32_nchw = (uint8_nchw.astype(np.float32) / 255.0)

        # Run Split ONNX (Backbone & Heads)
        split_outs = sess_split.run(None, {'images': fp32_nchw})
        fp32_bbox = split_outs[0] # [1, 64, 8400]
        fp32_cls  = split_outs[1] # [1, 3, 8400]

        fp32_bbox.tofile(f"/home/work_user2/kawachx_task/results/step7_htp_execution/fp32_reference/{name}_bbox_fp32.raw")
        fp32_cls.tofile(f"/home/work_user2/kawachx_task/results/step7_htp_execution/fp32_reference/{name}_class_fp32.raw")

        # Run Original ONNX (Full graph with DFL)
        orig_outs = sess_orig.run(None, {'images': fp32_nchw})
        orig_out0 = orig_outs[0] # [1, 7, 8400]
        orig_out0.tofile(f"/home/work_user2/kawachx_task/results/step7_htp_execution/fp32_reference/{name}_output0_fp32.raw")

        print(f"Generated FP32 reference for {name}: bbox shape {fp32_bbox.shape}, cls shape {fp32_cls.shape}")

if __name__ == "__main__":
    prepare()
