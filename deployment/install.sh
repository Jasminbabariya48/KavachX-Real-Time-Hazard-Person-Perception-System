#!/bin/bash
set -e
echo "=== Installing KavachX Production Service ==="

INSTALL_DIR="/home/work_user2/kawachx_task"
mkdir -p "$INSTALL_DIR/models" "$INSTALL_DIR/config" "$INSTALL_DIR/npu_worker" "$INSTALL_DIR/scripts/service" "$INSTALL_DIR/src/stream"

cp -v models/3class_calibrated_final.bin "$INSTALL_DIR/models/"
cp -v config/production_config.json "$INSTALL_DIR/config/"
cp -v config/kawach_worker.service "$INSTALL_DIR/config/"
cp -v scripts/service/kawach_service.py "$INSTALL_DIR/scripts/service/"

if [ -e /dev/fastrpc-cdsp ]; then
    echo "[PASS] FastRPC Device /dev/fastrpc-cdsp is accessible."
else
    echo "[WARN] /dev/fastrpc-cdsp not found! Ensure Qualcomm CDSP drivers are loaded."
fi

if id -nG "$USER" | grep -qw "render"; then
    echo "[PASS] User $USER belongs to group 'render'."
else
    echo "[WARN] User $USER is not in 'render' group. Run: sudo usermod -aG render $USER"
fi

echo "=== KavachX Installation Completed Successfully ==="
