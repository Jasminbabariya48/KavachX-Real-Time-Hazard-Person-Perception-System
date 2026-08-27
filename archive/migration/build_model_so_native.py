#!/usr/bin/env python3
import subprocess

def build_so():
    cmd = (
        'rm -rf /home/work_user2/kawachx_task/results/htp_compilation/build_native && '
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/build_native/jni && '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/Qnn* /home/work_user2/kawachx_task/results/htp_compilation/build_native/jni/ 2>/dev/null || true; '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_native/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_native/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.bin /home/work_user2/kawachx_task/results/htp_compilation/build_native/jni/ && '
        'cd /home/work_user2/kawachx_task/results/htp_compilation/build_native && '
        'make -f /home/devuser/qairt/2.47.0.260601/share/QNN/converter/Makefile.ubuntu-aarch64-gcc9.4 '
        'QNN_SDK_ROOT=/home/devuser/qairt/2.47.0.260601 '
        'TARGET_OBJCOPY_CMD="objcopy -I binary -O elf64-littleaarch64 -B aarch64" '
        'CXX=g++ '
        'QNN_MODEL_LIB_NAME=libmodel_qnn_int8; '
        'ls -la /home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== NATIVE MODEL SO BUILD OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    build_so()
