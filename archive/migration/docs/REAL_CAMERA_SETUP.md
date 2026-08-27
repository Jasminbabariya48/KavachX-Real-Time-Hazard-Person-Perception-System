# KavachX — Real Camera Setup & Ingestion Guide

## 1. Supported Ingestion Sources

KavachX supports three distinct live video ingestion modes configured via `config/production.json`:

### 1.1 Local V4L2 / USB / CSI Camera
Connect a USB or CSI camera to the EdgeBox. The device node is typically `/dev/video0`.
```json
{
  "stream": {
    "source_type": "camera",
    "source": "/dev/video0",
    "width": 1280,
    "height": 720,
    "target_fps": 30.0,
    "queue_maxsize": 2
  }
}
```

### 1.2 RTSP Network IP Camera
Stream from an IP security camera over RTSP with automatic backoff and reconnection:
```json
{
  "stream": {
    "source_type": "rtsp",
    "source": "rtsp://username:password@192.168.1.100:554/stream1",
    "reconnect_backoff_sec": 1.0,
    "max_reconnect_attempts": 5,
    "target_fps": 30.0,
    "queue_maxsize": 2
  }
}
```

### 1.3 Video File / Synthetic Stream
Stream from a local MP4/MKV video file for automated testing or evaluation:
```json
{
  "stream": {
    "source_type": "video",
    "source": "test_data/videos/live_test_stream.mp4",
    "capture_fps": 30.0,
    "loop": true
  }
}
```

---

## 2. Real-Time Bounded Queue Architecture
The pipeline enforces a **Latest-Frame-Wins** policy via `BoundedFrameQueue(maxsize=2)`.
If video capture exceeds DSP inference throughput, older frames are dropped instantly without memory accumulation, guaranteeing sub-second operator latency.
