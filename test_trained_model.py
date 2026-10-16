import os
import glob
from pathlib import Path
from PIL import Image
from chatbot.detector import get_detector, detect_vehicle_part, BEST_WEIGHTS, KNOWLEDGE_PATH
import json

BASE_DIR = Path(__file__).resolve().parent
TEST_IMAGES_DIR = BASE_DIR / "AI_MOTO_DATASET" / "test" / "images"

TARGET_CLASSES = [
    ("battery", ["BATTERY"]),
    ("spark_plug", ["SPARK-PLUG", "SPARK_PLUG"]),
    ("brake_rotor", ["BRAKE-ROTOR", "BRAKE_ROTOR"]),
    ("brake_pad", ["BRAKE-PAD", "BRAKE_PAD"]),
    ("brake_caliper", ["BRAKE-CALIPER", "BRAKE_CALIPER"]),
    ("radiator", ["RADIATOR"]),
    ("headlights", ["HEADLIGHTS"]),
    ("rim", ["RIM"]),
    ("oil_filter", ["OIL-FILTER", "OIL_FILTER"]),
    ("starter", ["STARTER"]),
    ("piston", ["PISTON"]),
    ("cylinder_head", ["CYLINDER-HEAD", "CYLINDER_HEAD"]),
    ("clutch_plate", ["CLUTCH-PLATE", "CLUTCH_PLATE"]),
    ("alternator", ["ALTERNATOR"]),
    ("transmission", ["TRANSMISSION"]),
    ("fuel_injector", ["FUEL-INJECTOR", "FUEL_INJECTOR"])
]

def run_evaluation():
    print("=" * 70)
    print("AI MOTO: YOLO11n Trained Model Evaluation & Unseen Image Testing")
    print("=" * 70)

    # 1. Verify weights
    print(f"\n[Step 1] Checking trained weights at: {BEST_WEIGHTS}")
    if BEST_WEIGHTS.exists():
        size_mb = os.path.getsize(BEST_WEIGHTS) / (1024 * 1024)
        print(f" -> Found fine-tuned best.pt ({size_mb:.2f} MB)")
    else:
        print(" -> Warning: best.pt not found yet. Using fallback weights.")

    # 2. Test 16 classes on unseen test images
    print("\n[Step 2] Testing Unseen Test Set Images Across All 16 Classes:")
    header = f"{'Class':<16} | {'Test Image File':<35} | {'Detected':<10} | {'Confidence':<10}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    results_table = []

    for class_name, prefixes in TARGET_CLASSES:
        # Find test image matching prefix
        matched_img = None
        for prefix in prefixes:
            pattern = str(TEST_IMAGES_DIR / f"{prefix}_*.*")
            matches = glob.glob(pattern)
            if matches:
                matched_img = matches[0]
                break
        
        if not matched_img:
            print(f"{class_name:<16} | {'No test image found':<35} | {'No':<10} | {'--':<10}")
            continue

        filename = os.path.basename(matched_img)
        # Run detection
        detection = detect_vehicle_part(matched_img, conf_threshold=0.25)
        
        detected_part = detection.get("part_class") or "None"
        conf = detection.get("confidence", 0.0)
        is_detected = "YES" if detection.get("detected") else "NO"

        print(f"{class_name:<16} | {filename[:33]:<35} | {is_detected:<10} | {conf:.2f}")
        results_table.append({
            "target": class_name,
            "image": filename,
            "detected": is_detected,
            "detected_class": detected_part,
            "confidence": conf
        })

    print("-" * len(header))

    # 3. Test Negative / Non-Vehicle Case
    print("\n[Step 3] Testing Negative / Non-Vehicle Image Rejection:")
    blank_img = Image.new('RGB', (640, 640), color=(128, 128, 128))
    neg_res = detect_vehicle_part(blank_img, conf_threshold=0.35)
    if not neg_res["detected"]:
        print(" -> PASSED: Blank non-vehicle image successfully rejected without false positive.")
    else:
        print(f" -> WARNING: Blank image falsely triggered {neg_res['part_class']}.")

    # 4. End-to-End Multimodal Knowledge Pipeline Verification
    print("\n[Step 4] Checking Multimodal Knowledge Pipeline Integration:")
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)
    print(f" -> Knowledge Base entries: {len(kb)} components verified.")
    sample_key = "brake_rotor"
    if sample_key in kb:
        info = kb[sample_key]
        print(f" -> Sample '{info['name']}':")
        print(f"    - Function: {info['function'][:60]}...")
        print(f"    - Working: {info['working'][:60]}...")
        print(f"    - Symptoms: {info['common_problems'][:2]}")

    print("\n" + "=" * 70)
    print("Evaluation Complete!")
    print("=" * 70)

if __name__ == "__main__":
    run_evaluation()
