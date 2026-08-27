"""Live Camera & Stream Inference Viewer."""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from kavachx.config.loader import load_config
from kavachx.capture.camera import create_capture_source
from kavachx.inference.engine import InferenceEngine
from kavachx.pipeline.events import AlertEventManager

def run_live_viewer(max_frames=20):
    cfg = load_config()
    source_cfg = cfg.get("stream", {})
    
    # If using video file, ensure path exists
    if source_cfg.get("source_type") == "video":
        vid_p = "/home/work_user2/kawachx_task/test_images/live_test_stream.mp4"
        if not os.path.exists(vid_p):
            vid_p = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_data/videos/live_test_stream.mp4"))
        source_cfg["source"] = vid_p
        
    src = create_capture_source(source_cfg)
    if not src.open():
        print(f"[ERROR] Could not open camera source: {source_cfg.get('source')}")
        return

    engine = InferenceEngine()
    if not engine.connect():
        print("[ERROR] Could not connect to NPU worker daemon. Is it running? (Run: python3 tools/service_manager.py start)")
        src.close()
        return

    event_mgr = AlertEventManager(cfg.get("alerting", {}))

    print("==================================================================")
    print("  KAVACHX REAL-TIME CAMERA INFERENCE (Qualcomm Hexagon v68 HTP DSP)")
    print(f"  Camera Source: {source_cfg.get('source_type', 'camera').upper()} ({source_cfg.get('source')})")
    print("==================================================================")

    for frame_idx in range(1, max_frames + 1):
        ok, frame, ts, f_id = src.read()
        if not ok or frame is None:
            print("[INFO] End of stream or frame capture timeout.")
            break

        out = engine.infer(frame, req_id=frame_idx)
        dispatched_alerts = event_mgr.process(out.detections)

        # Format detection objects
        if out.detections:
            det_summary = ", ".join([f"{d.class_name.upper()} ({d.confidence*100:.1f}%) [{d.bbox[0]:.0f},{d.bbox[1]:.0f},{d.bbox[2]:.0f},{d.bbox[3]:.0f}]" for d in out.detections])
        else:
            det_summary = "No objects detected"

        # Format alert tag
        if dispatched_alerts:
            alert_tag = f" 🚨 [{dispatched_alerts[0]['severity']}: {dispatched_alerts[0]['event_type']} - {dispatched_alerts[0]['class_name'].upper()}]"
        else:
            alert_tag = ""

        print(f"Frame #{frame_idx:02d} | DSP Latency: {out.infer_time_ms:5.2f} ms | Detections: {det_summary}{alert_tag}")
        time.sleep(0.04)

    src.close()
    engine.close()
    print("==================================================================")
    print("  Live camera stream finished successfully.")
    print("==================================================================")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_live_viewer(n)
