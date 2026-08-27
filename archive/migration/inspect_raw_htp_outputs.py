import numpy as np
import json
import os

def inspect_raw():
    samples = ['fire', 'fire_2', 'person']
    
    for s in samples:
        bbox_path = f"results/step7_htp_execution/raw/{s}_bbox_htp_int8.raw"
        cls_path = f"results/step7_htp_execution/raw/{s}_class_htp_int8.raw"
        
        if not os.path.exists(bbox_path):
            print(f"Missing {bbox_path}")
            continue
            
        bbox = np.fromfile(bbox_path, dtype=np.float32)
        cls = np.fromfile(cls_path, dtype=np.float32)
        
        print(f"\n=== Sample: {s} ===")
        print(f"  BBox elements: {bbox.size} (expected 64*8400={64*8400})")
        print(f"  BBox min: {bbox.min():.4f}, max: {bbox.max():.4f}, mean: {bbox.mean():.4f}")
        print(f"  BBox NaNs: {np.isnan(bbox).sum()}, Infs: {np.isinf(bbox).sum()}")
        
        print(f"  Class elements: {cls.size} (expected 3*8400={3*8400})")
        print(f"  Class min: {cls.min():.4f}, max: {cls.max():.4f}, mean: {cls.mean():.4f}")
        print(f"  Class NaNs: {np.isnan(cls).sum()}, Infs: {np.isinf(cls).sum()}")
        
        # Check layout: is it [1, 3, 8400] or [1, 8400, 3]?
        cls_3_8400 = cls.reshape(1, 3, 8400)
        cls_8400_3 = cls.reshape(1, 8400, 3)
        
        print(f"  If [1, 3, 8400]: class maxes across channels = {[float(cls_3_8400[0, c, :].max()) for c in range(3)]}")
        print(f"  If [1, 8400, 3]: class maxes across channels = {[float(cls_8400_3[0, :, c].max()) for c in range(3)]}")

if __name__ == "__main__":
    inspect_raw()
