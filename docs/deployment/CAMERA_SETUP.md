# Camera Setup Guide

KavachX supports three live ingestion modes:
1. **Local V4L2 USB/CSI Camera:** `/dev/video0` (1280x720 @ 30 FPS).
2. **RTSP Network IP Camera:** `rtsp://<user>:<pass>@<ip>:554/stream1` with automatic backoff reconnection.
3. **Video File Source:** `test_data/videos/live_test_stream.mp4` for validation.
