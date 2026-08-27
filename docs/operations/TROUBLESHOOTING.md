# Troubleshooting Guide

1. **FastRPC Permission Denied:** Ensure user is in `render` group (`sudo usermod -a -G render $USER`).
2. **Worker Socket Missing:** Check worker log at `/tmp/kawach_worker.log`.
