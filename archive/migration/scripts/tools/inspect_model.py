"""Model Inspection Tool for QNN / ONNX / Context Binaries."""
import os
import sys
import argparse
import hashlib

def inspect_model(model_path):
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return False
    sz = os.path.getsize(model_path)
    h = hashlib.sha256(open(model_path, "rb").read()).hexdigest()
    print(f"Model Path:   {model_path}")
    print(f"Size:         {sz} bytes ({sz / (1024*1024):.2f} MB)")
    print(f"SHA256:       {h}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KavachX Model Inspector")
    parser.add_argument("--model", type=str, default="models/production/3class_calibrated_final.bin")
    args = parser.parse_args()
    inspect_model(args.model)
