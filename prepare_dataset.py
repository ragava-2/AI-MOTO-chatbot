import os
import shutil
import yaml
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "car parts.v1i.yolov11"
DEST_DIR = BASE_DIR / "AI_MOTO_DATASET"

# 16 High-impact target classes matching our Vehicle Knowledge Base
TARGET_CLASSES = [
    "BATTERY",
    "BRAKE PAD",
    "BRAKE ROTOR",
    "BRAKE CALIPER",
    "SPARK PLUG",
    "RADIATOR",
    "HEADLIGHTS",
    "RIM",
    "OIL FILTER",
    "STARTER",
    "PISTON",
    "CYLINDER HEAD",
    "CLUTCH PLATE",
    "ALTERNATOR",
    "TRANSMISSION",
    "FUEL INJECTOR"
]

def prepare_dataset():
    if not SOURCE_DIR.exists():
        print(f"Error: Source dataset directory '{SOURCE_DIR}' not found.")
        return

    orig_yaml_path = SOURCE_DIR / "data.yaml"
    if not orig_yaml_path.exists():
        print(f"Error: 'data.yaml' not found in '{SOURCE_DIR}'.")
        return

    with open(orig_yaml_path, "r", encoding="utf-8") as f:
        orig_yaml = yaml.safe_load(f)
    orig_names = orig_yaml.get("names", [])

    # Map original class index -> new class index
    class_id_map = {}
    new_names = [name.lower().replace(" ", "_") for name in TARGET_CLASSES]
    for new_idx, name in enumerate(TARGET_CLASSES):
        if name in orig_names:
            orig_idx = orig_names.index(name)
            class_id_map[orig_idx] = new_idx
        else:
            print(f"Warning: Class '{name}' not found in original dataset names.")

    print(f"Mapped {len(class_id_map)} target classes out of {len(orig_names)} original classes.")

    # Create destination directories
    for split in ["train", "valid", "test"]:
        src_img_dir = SOURCE_DIR / split / "images"
        src_lbl_dir = SOURCE_DIR / split / "labels"

        dst_img_dir = DEST_DIR / split / "images"
        dst_lbl_dir = DEST_DIR / split / "labels"
        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        if not src_lbl_dir.exists():
            print(f"Skipping {split}, labels not found.")
            continue

        label_files = list(src_lbl_dir.glob("*.txt"))
        saved_count = 0

        for lbl_file in label_files:
            try:
                with open(lbl_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue

            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                orig_cls = int(parts[0])
                if orig_cls in class_id_map:
                    new_cls = class_id_map[orig_cls]
                    new_lines.append(f"{new_cls} {' '.join(parts[1:])}\n")

            # Only save if this image has at least one target class
            if new_lines:
                # Find matching image
                img_found = False
                for ext in [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG"]:
                    img_name = lbl_file.stem + ext
                    candidate_path = src_img_dir / img_name
                    if candidate_path.exists():
                        shutil.copy2(candidate_path, dst_img_dir / img_name)
                        img_found = True
                        break

                if img_found:
                    with open(dst_lbl_dir / lbl_file.name, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    saved_count += 1

        print(f"[{split}] Copied {saved_count} images with target annotations.")

    # Generate standardized data.yaml
    dest_yaml = {
        "path": str(DEST_DIR.as_posix()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(new_names),
        "names": new_names
    }

    yaml_out_path = DEST_DIR / "data.yaml"
    with open(yaml_out_path, "w", encoding="utf-8") as f:
        yaml.dump(dest_yaml, f, sort_keys=False)

    print(f"\nCreated clean dataset at: {DEST_DIR}")
    print(f"Dataset config written to: {yaml_out_path}")
    print(f"Classes ({len(new_names)}): {new_names}")

if __name__ == "__main__":
    prepare_dataset()
