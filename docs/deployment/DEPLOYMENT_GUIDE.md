# KavachX Deployment Guide

## Quick Deployment Steps
1. Verify user is member of `render` group (GID 993) for `/dev/fastrpc-cdsp` access.
2. Run installation:
```bash
bash deployment/install.sh
```
3. Start production worker service:
```bash
python3 tools/service_manager.py start
```
4. Verify daemon health:
```bash
cat /tmp/kawach_health.json
```
