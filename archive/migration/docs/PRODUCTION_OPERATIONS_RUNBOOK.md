# KavachX — Production Operations Runbook

## 1. System Overview
KavachX provides real-time hazard (fire, smoke) and person perception executing on the Qualcomm Hexagon v68 HTP DSP on the Radxa Dragon Q6490 / Kavach-EdgeBox platform.

---

## 2. Prerequisites & Environment
- **Operating System:** Linux 6.6 ARM64 (`aarch64-linux-gnu`)
- **NPU / DSP Acceleration:** Qualcomm Hexagon v68 HTP (FastRPC `/dev/fastrpc-cdsp`)
- **Required Group Membership:** `render` (GID `993`, permissions `0660`)
- **QAIRT SDK:** `2.47.0.260601` located at `/home/devuser/qairt/2.47.0.260601/`
- **Frozen Model Context Binary:** `models/3class_calibrated_final.bin` ($26,800,128\text{ bytes}$)

---

## 3. Installation Procedure
From the repository root or deployment package:
```bash
bash deployment/install.sh
```
This deploys model context binaries, configuration, and verifies FastRPC device permissions.

---

## 4. Service Lifecycle Management

### Start Service
```bash
python3 scripts/service/kawach_service.py start
```

### Check Service Health
```bash
cat /tmp/kawach_health.json
```
Expected output:
```json
{
  "service": "kawach_worker",
  "state": "READY",
  "details": {
    "pid": 217761,
    "model": "/home/work_user2/kawachx_task/models/3class_calibrated_final.bin",
    "socket": "/tmp/kawach_worker.sock"
  }
}
```

### Stop Service
```bash
python3 scripts/service/kawach_service.py stop
```

### Restart Service
```bash
python3 scripts/service/kawach_service.py restart
```

---

## 5. Live Stream & Web Monitoring
To launch the live stream pipeline and MJPEG web monitoring dashboard:
```bash
python3 -c "
import json
from src.stream.frame_source import create_frame_source
from src.stream.stream_pipeline import LiveStreamPipeline
from src.stream.live_monitoring_server import start_monitoring_server

with open('config/production_config.json') as f:
    cfg = json.load(f)

src = create_frame_source({'source_type': 'video', 'source': 'test_images/live_test_stream.mp4', 'capture_fps': 30.0, 'loop': True})
pipe = LiveStreamPipeline(cfg, src)
pipe.start()
start_monitoring_server(pipe, port=8080)
"
```
Access the live stream HUD at `http://<EDGEBOX_IP>:8080`.

---

## 6. Failure Recovery & Troubleshooting

| Symptom | Probable Cause | Action |
| :--- | :--- | :--- |
| `FastRPC /dev/fastrpc-cdsp: Permission Denied` | User not in `render` group | Verify `id $USER` includes `render (993)`. Request admin: `sudo usermod -aG render $USER`. |
| `Cannot connect to /tmp/kawach_worker.sock` | Worker is stopped or initializing | Run `python3 scripts/service/kawach_service.py restart` and check `/tmp/kawach_worker.log`. |
| `Stale process contention / high CPU` | Legacy test process running | Run `python3 scripts/testing/process_isolation.py` to audit and clean stale test runners. |

---

## 7. Model Checksum Integrity Verification
Verify that the deployed model context binary matches the frozen production signature:
```bash
sha256sum models/3class_calibrated_final.bin
```
Expected SHA256: `b7868a8c436fcf723fea7f95b3dcfd6f131fbe8ddb02ddf103addbe351dafabc`
