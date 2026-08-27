import onnxruntime as ort
import json

model_path = "/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx"
session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
meta = session.get_modelmeta()

print("Producer Name:", meta.producer_name)
print("Version:", meta.version)
print("Description:", meta.description)
print("Domain:", meta.domain)
print("Graph Name:", meta.graph_name)
print("Custom Metadata:")
for k, v in meta.custom_metadata_map.items():
    print(f"  {k}: {v}")
