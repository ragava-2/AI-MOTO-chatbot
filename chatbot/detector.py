import os
import json
import base64
import io
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
BEST_WEIGHTS = BASE_DIR / "weights" / "best.pt"
RUNS_WEIGHTS = BASE_DIR / "runs" / "detect" / "ai_moto_v1" / "weights" / "best.pt"
FALLBACK_WEIGHTS = BASE_DIR / "yolo11n.pt"
KNOWLEDGE_PATH = BASE_DIR / "data" / "vehicle_knowledge.json"

# Load vehicle knowledge base
_knowledge_base = {}
if KNOWLEDGE_PATH.exists():
    try:
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            _knowledge_base = json.load(f)
    except Exception as e:
        print(f"[Detector] Warning: Failed to load vehicle knowledge base: {e}")

_yolo_model = None
_model_loaded_path = None

def get_detector():
    """
    Lazy-loads the YOLO model to save startup memory.
    Prioritizes fine-tuned best.pt, then fallback yolo11n.pt.
    """
    global _yolo_model, _model_loaded_path
    
    weights_path = None
    if BEST_WEIGHTS.exists():
        weights_path = str(BEST_WEIGHTS)
    elif RUNS_WEIGHTS.exists():
        weights_path = str(RUNS_WEIGHTS)
    elif FALLBACK_WEIGHTS.exists():
        weights_path = str(FALLBACK_WEIGHTS)
        
    if not weights_path:
        return None

    if _yolo_model is not None and _model_loaded_path == weights_path:
        return _yolo_model

    try:
        from ultralytics import YOLO
        print(f"[Detector] Loading YOLO weights from: {weights_path}")
        _yolo_model = YOLO(weights_path)
        _model_loaded_path = weights_path
        return _yolo_model
    except Exception as e:
        print(f"[Detector] Error initializing YOLO model: {e}")
        return None

def detect_vehicle_part(image_source, conf_threshold=0.35):
    """
    Performs object detection on vehicle images.
    
    Args:
        image_source: Base64 string, raw bytes, Path, or PIL Image.
        conf_threshold: Minimum confidence score (default 0.35).
        
    Returns:
        dict containing:
            - detected: bool
            - part_class: str or None
            - confidence: float
            - bbox: list or None
            - knowledge: dict or None
            - prompt_context: str
    """
    result = {
        "detected": False,
        "part_class": None,
        "confidence": 0.0,
        "bbox": None,
        "knowledge": None,
        "prompt_context": ""
    }

    model = get_detector()
    if model is None:
        return result

    # Convert source to PIL image or file
    img = None
    try:
        if isinstance(image_source, str):
            # Check if base64 or path
            if os.path.exists(image_source):
                img = Image.open(image_source)
            else:
                # Treat as base64 string
                img_data = base64.b64decode(image_source)
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
        elif isinstance(image_source, bytes):
            img = Image.open(io.BytesIO(image_source)).convert("RGB")
        elif isinstance(image_source, Image.Image):
            img = image_source
        else:
            return result
    except Exception as e:
        print(f"[Detector] Failed to parse input image: {e}")
        return result

    try:
        # Run inference
        outputs = model(img, conf=conf_threshold, verbose=False)
        if not outputs or len(outputs[0].boxes) == 0:
            return result

        boxes = outputs[0].boxes
        # Get highest confidence detection
        best_idx = int(boxes.conf.argmax().item())
        cls_id = int(boxes.cls[best_idx].item())
        confidence = float(boxes.conf[best_idx].item())
        class_name = outputs[0].names[cls_id]
        clean_name = str(class_name).lower().strip().replace(" ", "_")

        xyxy = boxes.xyxy[best_idx].tolist()

        # Query knowledge base
        knowledge = _knowledge_base.get(clean_name)
        if not knowledge:
            # Try fuzzy match
            for k, val in _knowledge_base.items():
                if k in clean_name or clean_name in k:
                    knowledge = val
                    clean_name = k
                    break

        prompt_context = ""
        if knowledge:
            prompt_context = (
                f"\n\n[COMPUTER VISION OBJECT DETECTION]:\n"
                f"- Detected Component: {knowledge.get('name', clean_name)} ({confidence * 100:.1f}% confidence)\n"
                f"- Category: {knowledge.get('category', 'Automotive Part')}\n"
                f"- Primary Function: {knowledge.get('function', '')}\n"
                f"- How it Works: {knowledge.get('working', '')}\n"
                f"- Common Symptoms / Problems: {', '.join(knowledge.get('common_problems', []))}\n"
                f"- Recommended Maintenance: {', '.join(knowledge.get('maintenance', []))}\n"
                f"Instruction: Seamlessly incorporate this verified component knowledge and detection into your answer."
            )
        else:
            prompt_context = (
                f"\n\n[COMPUTER VISION OBJECT DETECTION]:\n"
                f"- Detected Component: {class_name} ({confidence * 100:.1f}% confidence).\n"
            )

        result["detected"] = True
        result["part_class"] = clean_name
        result["confidence"] = confidence
        result["bbox"] = xyxy
        result["knowledge"] = knowledge
        result["prompt_context"] = prompt_context

    except Exception as e:
        print(f"[Detector] Inference error: {e}")

    return result
