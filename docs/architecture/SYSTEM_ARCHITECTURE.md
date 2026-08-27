# KavachX System Architecture

## Overview
KavachX is an edge perception solution for real-time detection of fire, smoke, and persons, accelerated by the **Qualcomm Hexagon v68 HTP DSP** on Qualcomm QCS6490 hardware.

## Architecture Dataflow
```text
Live Stream (V4L2 Camera / RTSP / Video File)
       |
       v
Bounded Frame Queue (Latest-Frame Drop Policy)
       |
       v
Letterbox Preprocessor [1, 3, 640, 640] uint8 NCHW
       |
       v
FastRPC Zero-Copy Transport (/dev/fastrpc-cdsp)
       |
       v
Qualcomm Hexagon v68 HTP DSP (100% Neural Execution, 0 CPU Fallback)
       |
       v
Vectorized DFL Box & Class Decoder
       |
       v
Debounced Hazard Event Dispatcher (Fire: CRITICAL, Smoke: WARNING, Person: WARNING)
       |
       v
Monitoring Dashboard & Downstream Consumers
```
