"""Model Validation Tool."""
import os
import sys
import hashlib

EXPECTED_PRODUCTION_SHA256 = "b7868a8c436fcf723fea7f95b3dcfd6f131fbe8ddb02ddf103addbe351dafabc"

def validate_production_model(path="models/production/3class_calibrated_final.bin"):
    if not os.path.exists(path):
        path = "/home/work_user2/kawachx_task/models/3class_calibrated_final.bin"
    if not os.path.exists(path):
        print(f"[FAIL] Model file missing: {path}")
        return False
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if h == EXPECTED_PRODUCTION_SHA256:
        print(f"[PASS] Model signature matches production frozen checksum: {h}")
        return True
    else:
        print(f"[FAIL] Checksum mismatch! Expected {EXPECTED_PRODUCTION_SHA256}, got {h}")
        return False

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "models/production/3class_calibrated_final.bin"
    ok = validate_production_model(p)
    sys.exit(0 if ok else 1)
