# KavachX Production Deployment Package

## Overview
KavachX is a real-time hazard (fire, smoke) and person perception system running on the Qualcomm Hexagon v68 HTP DSP.

## Deployment Steps
1. Ensure Qualcomm QAIRT SDK 2.47.0.260601 is installed at `/home/devuser/qairt/2.47.0.260601/`.
2. Ensure current user is in `render` group (`/dev/fastrpc-cdsp`).
3. Run `bash install.sh`.
4. Start service: `python3 scripts/service/kawach_service.py start`.
5. Check health: `cat /tmp/kawach_health.json`.
