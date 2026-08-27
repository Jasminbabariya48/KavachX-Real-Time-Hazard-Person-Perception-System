# Production Go-Live Guide

Before production commissioning, run the acceptance verification:
```bash
make test
make demo
```
Verify `/tmp/kawach_health.json` indicates `READY` state.
