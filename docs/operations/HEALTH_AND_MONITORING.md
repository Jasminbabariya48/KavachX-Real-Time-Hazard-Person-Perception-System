# Health & Monitoring

The production daemon writes real-time health metrics to `/tmp/kawach_health.json`:
```json
{
  "service": "kawach_worker",
  "state": "READY",
  "details": {
    "pid": 253053,
    "model": "models/production/3class_calibrated_final.bin",
    "socket": "/tmp/kawach_worker.sock"
  }
}
```
