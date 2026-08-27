#!/bin/bash
echo "=== Uninstalling KavachX Service ==="
python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py stop 2>/dev/null || true
pkill -9 kawach_worker 2>/dev/null || true
rm -f /tmp/kawach_worker.sock /tmp/kawach_health.json /tmp/kawach_worker.log
echo "=== KavachX Service Cleaned ==="
