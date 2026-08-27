import onnx
from onnx import helper, TensorProto
import subprocess
import json
import os

def run_experiment_1():
    orig_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx'
    exp_onnx = '/home/work_user2/kawachx_task/models/model_exp1_pyramids.onnx'
    
    print("=== Experiment 1: Extract 6 4D Convolutional Pyramid Heads ===")
    # The 6 convolution outputs before Reshape/Concat in YOLOv8 head:
    # Bbox heads:
    # 1. /model.22/cv2.0/cv2.0.2/Conv_output_0 (shape: [1, 64, 80, 80])
    # 2. /model.22/cv2.1/cv2.1.2/Conv_output_0 (shape: [1, 64, 40, 40])
    # 3. /model.22/cv2.2/cv2.2.2/Conv_output_0 (shape: [1, 64, 20, 20])
    # Class heads:
    # 4. /model.22/cv3.0/cv3.0.2/Conv_output_0 (shape: [1, 3, 80, 80])
    # 5. /model.22/cv3.1/cv3.1.2/Conv_output_0 (shape: [1, 3, 40, 40])
    # 6. /model.22/cv3.2/cv3.2.2/Conv_output_0 (shape: [1, 3, 20, 20])
    
    target_outputs = [
        '/model.22/cv2.0/cv2.0.2/Conv_output_0',
        '/model.22/cv2.1/cv2.1.2/Conv_output_0',
        '/model.22/cv2.2/cv2.2.2/Conv_output_0',
        '/model.22/cv3.0/cv3.0.2/Conv_output_0',
        '/model.22/cv3.1/cv3.1.2/Conv_output_0',
        '/model.22/cv3.2/cv3.2.2/Conv_output_0',
    ]
    
    model = onnx.load(orig_path)
    graph = model.graph
    
    needed_tensors = set(target_outputs)
    nodes_to_keep = []
    
    for node in reversed(graph.node):
        if any(out in needed_tensors for out in node.output):
            nodes_to_keep.append(node)
            for inp in node.input:
                if inp:
                    needed_tensors.add(inp)
                    
    nodes_to_keep.reverse()
    initializers_to_keep = [init for init in graph.initializer if init.name in needed_tensors]
    
    new_outputs = [
        helper.make_tensor_value_info('/model.22/cv2.0/cv2.0.2/Conv_output_0', TensorProto.FLOAT, [1, 64, 80, 80]),
        helper.make_tensor_value_info('/model.22/cv2.1/cv2.1.2/Conv_output_0', TensorProto.FLOAT, [1, 64, 40, 40]),
        helper.make_tensor_value_info('/model.22/cv2.2/cv2.2.2/Conv_output_0', TensorProto.FLOAT, [1, 64, 20, 20]),
        helper.make_tensor_value_info('/model.22/cv3.0/cv3.0.2/Conv_output_0', TensorProto.FLOAT, [1, 3, 80, 80]),
        helper.make_tensor_value_info('/model.22/cv3.1/cv3.1.2/Conv_output_0', TensorProto.FLOAT, [1, 3, 40, 40]),
        helper.make_tensor_value_info('/model.22/cv3.2/cv3.2.2/Conv_output_0', TensorProto.FLOAT, [1, 3, 20, 20]),
    ]
    
    new_graph = helper.make_graph(
        nodes=nodes_to_keep,
        name='kavachx_3class_pyramids',
        inputs=list(graph.input),
        outputs=new_outputs,
        initializer=initializers_to_keep
    )
    new_model = helper.make_model(new_graph, producer_name='kavachx_exp1', opset_imports=model.opset_import)
    onnx.checker.check_model(new_model)
    onnx.save(new_model, exp_onnx)
    print(f"Saved {exp_onnx} (Nodes: {len(nodes_to_keep)})")
    
    # 2. QNN INT8 Conversion
    conv_cmd = (
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1 && '
        'qnn-onnx-converter '
        '--input_network /home/work_user2/kawachx_task/models/model_exp1_pyramids.onnx '
        '-o /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/model_exp1.cpp '
        '--input_list /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt '
        '--act_bw 8 --weight_bw 8 --bias_bw 32 --use_per_channel_quantization '
        '> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/conv_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/conv_stderr.log'
    )
    print("Running QNN conversion for Exp 1...")
    res_conv = subprocess.run(conv_cmd, shell=True, executable='/bin/bash')
    print("Conv RC:", res_conv.returncode)
    
    # 3. Build model SO
    build_cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/jni && '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/Qnn* /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/jni/ 2>/dev/null || true; '
        'cp /home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/jni/ && '
        'cp /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/model_exp1.cpp /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/jni/ && '
        'cp /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/model_exp1.bin /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/jni/ && '
        'cd /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build && '
        'make -f /home/devuser/qairt/2.47.0.260601/share/QNN/converter/Makefile.ubuntu-aarch64-gcc9.4 '
        'QNN_SDK_ROOT=/home/devuser/qairt/2.47.0.260601 '
        'TARGET_OBJCOPY_CMD="objcopy -I binary -O elf64-littleaarch64 -B aarch64" '
        'CXX=g++ '
        'QNN_MODEL_LIB_NAME=libmodel_exp1 '
        '> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build_stderr.log'
    )
    print("Building shared library for Exp 1...")
    res_build = subprocess.run(build_cmd, shell=True, executable='/bin/bash')
    print("Build RC:", res_build.returncode)

    # 4. HTP compilation
    gen_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/build/libs/aarch64-ubuntu-gcc9.4/libmodel_exp1.so '
        '/home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/kavachx_3class_exp1_htp_v68.bin '
        '> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/context_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/context_stderr.log; '
        'echo "Context Gen RC: $?"; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/context_stdout.log; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/context_stderr.log; '
        'ls -lh /home/work_user2/kawachx_task/results/htp_compilation_split/experiments/exp1/kavachx_3class_exp1_htp_v68.bin'
    )
    print("Running HTP compilation for Exp 1...")
    res_gen = subprocess.run(gen_cmd, shell=True, executable='/bin/bash', capture_output=True, text=True)
    print("=== EXP 1 HTP GEN OUTPUT ===")
    print(res_gen.stdout)
    if res_gen.stderr:
        print("STDERR:\n", res_gen.stderr)

if __name__ == "__main__":
    run_experiment_1()
