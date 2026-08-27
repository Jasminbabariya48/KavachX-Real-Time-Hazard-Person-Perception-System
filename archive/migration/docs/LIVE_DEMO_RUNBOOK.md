# KavachX — Live Demonstration Runbook

## 1. Objective
This runbook outlines the exact sequence for presenting a deterministic, interactive live demonstration of KavachX on Qualcomm Hexagon v68 HTP DSP hardware.

---

## 2. Interactive Demonstration Steps

### Step 1: Pre-Flight & Health Inspection
```bash
python3 scripts/service/kawach_service.py status
cat /tmp/kawach_health.json
```
**Show to Evaluators:**
- Service state is `READY`.
- FastRPC device `/dev/fastrpc-cdsp` is active.
- Context binary `models/3class_calibrated_final.bin` is mapped into DSP memory.

---

### Step 2: Bounded Live Stream Demonstration
Run a bounded 30-frame live video inference sequence:
```bash
python3 scripts/testing/bounded_stream_runner.py \
  --test-name "Evaluation_Live_Demo" \
  --source test_images/live_test_stream.mp4 \
  --max-frames 30 \
  --duration-seconds 4.0 \
  --hard-timeout-seconds 6.0
```
**Demonstrated Outputs:**
- **Perception Output:** Real-time detections for `fire`, `smoke`, and `person` with unpadded bounding boxes.
- **Hardware Acceleration:** $100\%$ Qualcomm Hexagon v68 HTP DSP execution (Mean latency: $\sim 60\text{ ms}$, CPU Fallback = 0).
- **Graceful Termination:** Automatic completion upon reaching frame limits.

---

### Step 3: Fault-Tolerance Demonstration (Abrupt Disconnect & Recovery)
```bash
python3 -c "
import socket, struct, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/tmp/kawach_worker.sock')
s.sendall(struct.pack('=IIII', 0x4B574158, 999, 1000000, 0) + b'\x00'*100)
s.close()
print('Injected abrupt disconnect!')
"
python3 scripts/testing/bounded_stream_runner.py --test-name "Post_Disconnect_Proof" --max-frames 10 --duration-seconds 2.0
```
**Demonstrated Outputs:**
- The production worker gracefully handles the broken pipe, retains DSP context, and serves subsequent requests without restarting.

---

### Step 4: Clean Teardown
```bash
python3 scripts/testing/process_isolation.py
```
**Show to Evaluators:**
- Target process audit confirms $0$ zombie processes and clean socket state.
