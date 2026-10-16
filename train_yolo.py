import os
from pathlib import Path
import torch
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATA_YAML = BASE_DIR / "AI_MOTO_DATASET" / "data.yaml"
BASE_WEIGHT = BASE_DIR / "yolo11n.pt"

def train_ai_moto_detector(epochs=35, batch=4, imgsz=640, workers=0, resume=False):
    if not DATA_YAML.exists():
        print(f"Error: {DATA_YAML} not found. Please run prepare_dataset.py first.")
        return

    # Check hardware
    if torch.cuda.is_available():
        device = "0"
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"Using GPU acceleration: {gpu_name} ({vram_gb:.2f} GB VRAM)")
        torch.cuda.empty_cache()
    else:
        device = "cpu"
        print("CUDA GPU not detected. Using optimized multi-thread CPU training.")

    last_weights = BASE_DIR / "runs" / "detect" / "ai_moto_v1" / "weights" / "last.pt"

    # Handle resume or new training
    if resume and last_weights.exists():
        print(f"Resuming training from checkpoint: {last_weights}")
        model = YOLO(str(last_weights))
        results = model.train(resume=True)
    else:
        weights_to_load = str(BASE_WEIGHT) if BASE_WEIGHT.exists() else "yolo11n.pt"
        print(f"Loading base YOLO11n weights from: {weights_to_load}")
        model = YOLO(weights_to_load)

        print(f"Starting training on {DATA_YAML} for {epochs} epochs (batch={batch}, workers={workers})...")
        results = model.train(
            data=str(DATA_YAML),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            workers=workers,
            project=str(BASE_DIR / "runs" / "detect"),
            name="ai_moto_v1",
            exist_ok=True,
            save=True,
            patience=10,
            verbose=True
        )

    best_weights = BASE_DIR / "runs" / "detect" / "ai_moto_v1" / "weights" / "best.pt"
    print(f"\nTraining completed!")
    if best_weights.exists():
        print(f"Best fine-tuned weights saved at: {best_weights}")
    return results

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AI MOTO YOLO11n Vehicle Part Detector")
    parser.add_argument("--epochs", type=int, default=35, help="Number of training epochs (default: 35)")
    parser.add_argument("--batch", type=int, default=4, help="Batch size (default: 4 for 4GB VRAM safety)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size (default: 640)")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers (default: 0 on Windows)")
    parser.add_argument("--resume", action="store_true", help="Resume training from last.pt checkpoint")
    args = parser.parse_args()

    train_ai_moto_detector(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        workers=args.workers,
        resume=args.resume
    )
