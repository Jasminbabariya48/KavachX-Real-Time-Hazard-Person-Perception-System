#!/usr/bin/env python3
import subprocess

def test_simple_model():
    script = (
        'python3 -c "'
        'import torch, torch.nn as nn\n'
        'class SimpleNet(nn.Module):\n'
        '    def __init__(self): super().__init__(); self.c = nn.Conv2d(3, 16, 3, padding=1); self.r = nn.ReLU()\n'
        '    def forward(self, x): return self.r(self.c(x))\n'
        'm = SimpleNet().eval()\n'
        'torch.onnx.export(m, torch.randn(1, 3, 640, 640), \'/home/work_user2/kawachx_task/models/simple.onnx\', input_names=[\'images\'], output_names=[\'output\'])\n'
        '" && '
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'qnn-onnx-converter -i /home/work_user2/kawachx_task/models/simple.onnx -o /home/work_user2/kawachx_task/results/htp_compilation/simple_qnn.cpp --input_list /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt --act_bw 8 --weight_bw 8 --bias_bw 32 && '
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/build_simple/jni && '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/Qnn* /home/work_user2/kawachx_task/results/htp_compilation/build_simple/jni/ 2>/dev/null || true; '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_simple/jni/ && '
        'cp /home/work_user2/kawachx_task/results/htp_compilation/simple_qnn.cpp /home/work_user2/kawachx_task/results/htp_compilation/build_simple/jni/ && '
        'cp /home/work_user2/kawachx_task/results/htp_compilation/simple_qnn.bin /home/work_user2/kawachx_task/results/htp_compilation/build_simple/jni/ && '
        'cd /home/work_user2/kawachx_task/results/htp_compilation/build_simple && '
        'make -f /home/devuser/qairt/2.47.0.260601/share/QNN/converter/Makefile.ubuntu-aarch64-gcc9.4 '
        'QNN_SDK_ROOT=/home/devuser/qairt/2.47.0.260601 '
        'TARGET_OBJCOPY_CMD="objcopy -I binary -O elf64-littleaarch64 -B aarch64" '
        'CXX=g++ '
        'QNN_MODEL_LIB_NAME=libsimple_qnn && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/build_simple/libs/aarch64-ubuntu-gcc9.4/libsimple_qnn.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/output/simple_htp_v68.bin; '
        'echo "Simple Net RC: $?"; '
        'ls -la /home/work_user2/kawachx_task/results/htp_compilation/output/simple_htp_v68.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', script], capture_output=True, text=True)
    print("=== SIMPLE NET TEST ===")
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    test_simple_model()
