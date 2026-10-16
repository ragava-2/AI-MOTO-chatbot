import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from chatbot.detector import detect_vehicle_part, get_detector, _knowledge_base

def test_pipeline():
    print("==================================================")
    print("Testing AI MOTO Vision Pipeline")
    print("==================================================")
    
    # 1. Test Knowledge Base
    print(f"\n[1] Knowledge Base Check:")
    print(f"Loaded {len(_knowledge_base)} vehicle components:")
    for key in list(_knowledge_base.keys())[:5]:
        item = _knowledge_base[key]
        print(f"  - {key}: {item['name']} ({item['category']})")
        
    assert "battery" in _knowledge_base, "battery missing from knowledge base"
    assert "spark_plug" in _knowledge_base, "spark_plug missing from knowledge base"
    assert "brake_rotor" in _knowledge_base, "brake_rotor missing from knowledge base"
    print("[OK] Knowledge Base verified.")

    # 2. Test Model Detector Initialization
    print(f"\n[2] YOLO11 Detector Initialization:")
    model = get_detector()
    if model is not None:
        print(f"[OK] Detector successfully initialized with weights.")
    else:
        print("[INFO] Model not loaded yet (weights not found).")

    # 3. Test Synthetic Image Inference
    print(f"\n[3] Running Synthetic Test Image Inference:")
    test_img = Image.new("RGB", (640, 640), color=(70, 70, 70))
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([100, 100, 300, 300], fill=(200, 50, 50))
    
    res = detect_vehicle_part(test_img, conf_threshold=0.25)
    print(f"Detection Result: detected={res['detected']}, part={res['part_class']}, confidence={res['confidence']:.2f}")
    if res['prompt_context']:
        print(f"Prompt Context Preview:\n{res['prompt_context'][:200]}...")
    # 4. Test with Real Dataset Image
    print(f"\n[4] Running Detection on Real Dataset Image:")
    val_img_dir = BASE_DIR / "AI_MOTO_DATASET" / "valid" / "images"
    if val_img_dir.exists():
        sample_imgs = list(val_img_dir.glob("*.jpg"))
        if sample_imgs:
            sample_path = str(sample_imgs[0])
            print(f"Testing on image: {Path(sample_path).name}")
            real_res = detect_vehicle_part(sample_path, conf_threshold=0.15)
            print(f"Real Image Detection: detected={real_res['detected']}, part={real_res['part_class']}, confidence={real_res['confidence']:.2f}")
            if real_res['knowledge']:
                print(f"Knowledge Retrieved: {real_res['knowledge']['name']} - Function: {real_res['knowledge']['function'][:80]}...")
    
    print("[OK] Pipeline runs end-to-end without exceptions.")
    print("==================================================")

if __name__ == "__main__":
    test_pipeline()
