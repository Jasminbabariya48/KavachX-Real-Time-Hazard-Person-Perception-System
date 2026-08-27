"""Artifact and Manifest Verification Tool."""
import os
import sys
import json
import hashlib

def verify_manifest(manifest_path="artifacts/manifests/production_manifest.json"):
    if not os.path.exists(manifest_path):
        manifest_path = "results/step11_final/production_manifest.json"
    if not os.path.exists(manifest_path):
        print(f"[FAIL] Manifest missing: {manifest_path}")
        return False
    with open(manifest_path, "r") as f:
        items = json.load(f)
    print(f"Verifying {len(items)} artifacts...")
    all_ok = True
    for item in items:
        p = item["path"]
        if os.path.exists(p):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            match = (h == item["sha256"])
            print(f"  [{'PASS' if match else 'FAIL'}] {item['artifact']}: {p}")
            if not match: all_ok = False
        else:
            print(f"  [MISSING] {item['artifact']}: {p}")
            if item.get("required_for_production", True):
                all_ok = False
    return all_ok

if __name__ == "__main__":
    ok = verify_manifest()
    sys.exit(0 if ok else 1)
