# KavachX Architecture Overview

## Dataflow Architecture
```text
Camera / Video Stream (app/camera)
       |
       v
Bounded Frame Queue (app/pipeline)
       |
       v
Letterbox Preprocessor (app/inference)
       |
       v
NPU FastRPC Engine (native/npu_worker) ---> Qualcomm Hexagon v68 HTP DSP
       |
       v
Vectorized DFL Box Decoder (app/inference)
       |
       v
Event Manager & Debouncer (app/events) ---> Alerts (CRITICAL / WARNING)
```
