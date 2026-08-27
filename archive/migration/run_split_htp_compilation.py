#!/usr/bin/env python3
import subprocess
import os

def compile_split_htp():
    # 1. Prepare target directories
    prep_cmd = (
        'rm -rf /home/work_user2/kawachx_task/results/htp_compilation_split && '
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation_split/{build,output,logs,reports,experiments}'
    )
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', prep_cmd], check=True)

    # 2. Build model shared library (.so)
    build_so_cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation_split/build/jni && '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/Qnn* /home/work_user2/kawachx_task/results/htp_compilation_split/build/jni/ 2>/dev/null || true; '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp /home/work_user2/kawachx_task/results/htp_compilation_split/build/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/generated/model_split_qnn_int8.cpp /home/work_user2/kawachx_task/results/htp_compilation_split/build/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/generated/model_split_qnn_int8.bin /home/work_user2/kawachx_task/results/htp_compilation_split/build/jni/ && '
        'cd /home/work_user2/kawachx_task/results/htp_compilation_split/build && '
        'make -f /home/devuser/qairt/2.47.0.260601/share/QNN/converter/Makefile.ubuntu-aarch64-gcc9.4 '
        'QNN_SDK_ROOT=/home/devuser/qairt/2.47.0.260601 '
        'TARGET_OBJCOPY_CMD="objcopy -I binary -O elf64-littleaarch64 -B aarch64" '
        'CXX=g++ '
        'QNN_MODEL_LIB_NAME=libmodel_split_qnn_int8 '
        '> /home/work_user2/kawachx_task/results/htp_compilation_split/logs/build_so_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation_split/logs/build_so_stderr.log; '
        'echo "Build SO RC: $?"; '
        'ls -lh libs/aarch64-ubuntu-gcc9.4/libmodel_split_qnn_int8.so'
    )
    print("=== Step 1: Building Model Shared Library ===")
    res1 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', build_so_cmd], capture_output=True, text=True)
    print(res1.stdout)
    if res1.stderr:
        print("STDERR:\n", res1.stderr)

    # 3. Generate HTP v68 Context Binary
    gen_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation_split/build/libs/aarch64-ubuntu-gcc9.4/libmodel_split_qnn_int8.so '
        '/home/work_user2/kawachx_task/results/htp_compilation_split/output/kavachx_3class_int8_htp_v68.bin '
        '> /home/work_user2/kawachx_task/results/htp_compilation_split/logs/context_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation_split/logs/context_gen_stderr.log; '
        'echo "Context Gen RC: $?"; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation_split/logs/context_gen_stdout.log; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation_split/logs/context_gen_stderr.log; '
        'ls -lh /home/work_user2/kawachx_task/results/htp_compilation_split/output/kavachx_3class_int8_htp_v68.bin; '
        'sha256sum /home/work_user2/kawachx_task/results/htp_compilation_split/output/kavachx_3class_int8_htp_v68.bin > /home/work_user2/kawachx_task/results/htp_compilation_split/reports/checksum.txt; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation_split/reports/checksum.txt'
    )
    print("=== Step 2: Compiling Context Binary for Hexagon v68 HTP ===")
    res2 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', gen_cmd], capture_output=True, text=True)
    print(res2.stdout)
    if res2.stderr:
        print("STDERR:\n", res2.stderr)

if __name__ == "__main__":
    compile_split_htp()
