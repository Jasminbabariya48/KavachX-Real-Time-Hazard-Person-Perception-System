#!/usr/bin/env python3
import subprocess

def test_float_fallback():
    # 1. Convert with float fallback
    conv_cmd = (
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'qnn-onnx-converter '
        '--input_network /home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx '
        '-o /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_fallback.cpp '
        '--input_list /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt '
        '--act_bw 8 --weight_bw 8 --bias_bw 32 --use_per_channel_quantization '
        '--float_fallback'
    )
    print("=== Step 1: Converting with --float_fallback ===")
    res1 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', conv_cmd], capture_output=True, text=True)
    print(res1.stdout)
    if res1.stderr:
        print("STDERR:\n", res1.stderr)
        
    # 2. Build model SO
    build_cmd = (
        'rm -rf /home/work_user2/kawachx_task/results/htp_compilation/build_fallback && '
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/build_fallback/jni && '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/Qnn* /home/work_user2/kawachx_task/results/htp_compilation/build_fallback/jni/ 2>/dev/null || true; '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_fallback/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_fallback.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_fallback/jni/ && '
        'cp /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_fallback.bin /home/work_user2/kawachx_task/results/htp_compilation/build_fallback/jni/ && '
        'cd /home/work_user2/kawachx_task/results/htp_compilation/build_fallback && '
        'make -f /home/devuser/qairt/2.47.0.260601/share/QNN/converter/Makefile.ubuntu-aarch64-gcc9.4 '
        'QNN_SDK_ROOT=/home/devuser/qairt/2.47.0.260601 '
        'TARGET_OBJCOPY_CMD="objcopy -I binary -O elf64-littleaarch64 -B aarch64" '
        'CXX=g++ '
        'QNN_MODEL_LIB_NAME=libmodel_fallback; '
        'ls -la libs/aarch64-ubuntu-gcc9.4/'
    )
    print("=== Step 2: Building Shared Library ===")
    res2 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', build_cmd], capture_output=True, text=True)
    print(res2.stdout)
    if res2.stderr:
        print("STDERR:\n", res2.stderr)

    # 3. Run Generator
    gen_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/build_fallback/libs/aarch64-ubuntu-gcc9.4/libmodel_fallback.so '
        '/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin'
    )
    print("=== Step 3: Generating Context Binary ===")
    res3 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', gen_cmd], capture_output=True, text=True)
    print(res3.stdout)
    if res3.stderr:
        print("STDERR:\n", res3.stderr)

if __name__ == "__main__":
    test_float_fallback()
