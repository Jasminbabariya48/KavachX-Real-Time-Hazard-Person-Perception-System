"""Model Inspection Tool."""
import os
import sys
import hashlib

def inspect(model_path="models/production/3class_calibrated_final.bin"):
    if not os.path.exists(model_path):
        print(f"Model missing: {model_path}")
        return
    sz = os.path.getsize(model_path)
    sha = hashlib.sha256(open(model_path, "rb").read()).hexdigest()
    print(f"Model:  {model_path}")
    print(f"Size:   {sz} bytes ({sz/(1024*1024):.2f} MB)")
    print(f"SHA256: {sha}")

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "models/production/3class_calibrated_final.bin"
    inspect(p)
