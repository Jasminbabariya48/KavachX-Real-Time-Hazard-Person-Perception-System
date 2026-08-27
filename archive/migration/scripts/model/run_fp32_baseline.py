#!/usr/bin/env python3
"""
FP32 ONNX Runtime Reference Baseline Execution on Kavach-EdgeBox
Exact Ultralytics Class Mapping: {0: 'person', 1: 'fire', 2: 'smoke'}
"""

import os
import sys
import time
import json
import glob
import numpy as np
import cv2
import onnxruntime as ort

CLASS_NAMES = {0: 'person', 1: 'fire', 2: 'smoke'}

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

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
    return img, r, (dw, dh)

def postprocess_yolov8(output, conf_thresh=0.25, iou_thresh=0.45, ratio=1.0, pad=(0, 0), orig_shape=(640, 640)):
    predictions = np.squeeze(output)
    if predictions.shape[0] == 7 and predictions.shape[1] == 8400:
        predictions = predictions.T

    boxes = predictions[:, :4]  # cx, cy, w, h
    scores = predictions[:, 4:] # 3 classes: Person (0), Fire (1), Smoke (2)

    class_ids = np.argmax(scores, axis=1)
    confidences = np.max(scores, axis=1)

    mask = confidences >= conf_thresh
    boxes = boxes[mask]
    scores = confidences[mask]
    class_ids = class_ids[mask]

    if len(boxes) == 0:
        return []

    x1 = (boxes[:, 0] - boxes[:, 2] / 2 - pad[0]) / ratio
    y1 = (boxes[:, 1] - boxes[:, 3] / 2 - pad[1]) / ratio
    x2 = (boxes[:, 0] + boxes[:, 2] / 2 - pad[0]) / ratio
    y2 = (boxes[:, 1] + boxes[:, 3] / 2 - pad[1]) / ratio

    x1 = np.clip(x1, 0, orig_shape[1])
    y1 = np.clip(y1, 0, orig_shape[0])
    x2 = np.clip(x2, 0, orig_shape[1])
    y2 = np.clip(y2, 0, orig_shape[0])

    cv_boxes = [[int(x1[i]), int(y1[i]), int(x2[i] - x1[i]), int(y2[i] - y1[i])] for i in range(len(x1))]
    indices = cv2.dnn.NMSBoxes(cv_boxes, scores.tolist(), conf_thresh, iou_thresh)

    detections = []
    if len(indices) > 0:
        for i in indices.flatten():
            detections.append({
                "class_id": int(class_ids[i]),
                "class_name": CLASS_NAMES.get(int(class_ids[i]), f"class_{class_ids[i]}"),
                "confidence": float(scores[i]),
                "bbox": [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])]
            })
    return detections

def main():
    model_path = os.path.expanduser("~/kawachx_task/models/new_3class_best_FP32.onnx")
    images_dir = os.path.expanduser("~/kawachx_task/test_images")
    output_dir = os.path.expanduser("~/kawachx_task/results/fp32_baseline")
    raw_out_dir = os.path.join(output_dir, "raw_outputs")
    vis_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(raw_out_dir, exist_ok=True)
    os.makedirs(vis_dir, exist_ok=True)

    print("================================================================")
    print(" FP32 ONNX Runtime CPU Reference Execution")
    print(f" Model: {model_path}")
    print("================================================================")

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(model_path, opts, providers=['CPUExecutionProvider'])

    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]

    image_files = sorted(glob.glob(os.path.join(images_dir, "*.jpg")))
    all_results = {}
    latencies = []

    # Warmup
    dummy_input = np.zeros(input_meta.shape, dtype=np.float32)
    for _ in range(5):
        session.run([output_meta.name], {input_meta.name: dummy_input})

    for img_path in image_files:
        img_name = os.path.basename(img_path)
        img = cv2.imread(img_path)
        orig_h, orig_w = img.shape[:2]

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        padded_img, ratio, pad = letterbox(img_rgb, (640, 640))
        input_tensor = padded_img.astype(np.float32) / 255.0
        input_tensor = np.transpose(input_tensor, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)

        t0 = time.perf_counter()
        outputs = session.run([output_meta.name], {input_meta.name: input_tensor})
        t1 = time.perf_counter()
        infer_time_ms = (t1 - t0) * 1000.0
        latencies.append(infer_time_ms)

        raw_output = outputs[0]
        raw_out_path = os.path.join(raw_out_dir, f"{os.path.splitext(img_name)[0]}_raw.npy")
        np.save(raw_out_path, raw_output)

        detections = postprocess_yolov8(raw_output, conf_thresh=0.25, iou_thresh=0.45, ratio=ratio, pad=pad, orig_shape=(orig_h, orig_w))

        # Visual overlay
        vis_img = img.copy()
        for d in detections:
            box = [int(x) for x in d['bbox']]
            color = (0, 0, 255) if d['class_name'] == 'fire' else ((128, 128, 128) if d['class_name'] == 'smoke' else (0, 255, 0))
            cv2.rectangle(vis_img, (box[0], box[1]), (box[2], box[3]), color, 2)
            label = f"{d['class_name']} {d['confidence']*100:.1f}%"
            cv2.putText(vis_img, label, (box[0], max(20, box[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        vis_path = os.path.join(vis_dir, f"{os.path.splitext(img_name)[0]}_pred.jpg")
        cv2.imwrite(vis_path, vis_img)

        all_results[img_name] = {
            "image_dimensions": [orig_w, orig_h],
            "inference_time_ms": infer_time_ms,
            "num_detections": len(detections),
            "detections": detections,
            "raw_output_file": raw_out_path,
            "visualization_file": vis_path
        }

        print(f"\n--- Image: {img_name} ({orig_w}x{orig_h}) ---")
        print(f"Inference Latency: {infer_time_ms:.2f} ms")
        print(f"Detections Count: {len(detections)}")
        for d in detections:
            print(f" - [{d['class_name'].upper()}] Confidence: {d['confidence']*100:.1f}%, BBox: {[round(x, 1) for x in d['bbox']]}")

    report = {
        "model_path": model_path,
        "input_shape": input_meta.shape,
        "output_shape": output_meta.shape,
        "class_mapping": CLASS_NAMES,
        "latency_stats": {
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "min_ms": float(np.min(latencies)),
            "max_ms": float(np.max(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "throughput_fps": float(1000.0 / np.mean(latencies))
        },
        "per_image_results": all_results
    }

    report_path = os.path.join(output_dir, "fp32_baseline_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n================================================================")
    print(f" FP32 Baseline Report written to: {report_path}")
    print(f" Mean Latency: {report['latency_stats']['mean_ms']:.2f} ms ({report['latency_stats']['throughput_fps']:.1f} FPS)")
    print(f"================================================================")

if __name__ == "__main__":
    main()
