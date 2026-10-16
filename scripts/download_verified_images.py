import os
import io
import urllib.request
import json
from PIL import Image

TARGETS = [
    ("Honda_Activa", "honda_activa_6g.jpg"),
    ("Bajaj_Pulsar", "bajaj_pulsar_150.jpg"),
    ("KTM_390_series", "ktm_duke_390.jpg"),
    ("Hyundai_Creta", "hyundai_creta.jpg")
]

DEST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "vehicles")
os.makedirs(DEST_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for title, fname in TARGETS:
    target_path = os.path.join(DEST_DIR, fname)
    if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
        print(f"Already exists: {fname}")
        continue

    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    req = urllib.request.Request(api_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            img_meta = data.get("originalimage") or data.get("thumbnail")
            if not img_meta:
                print(f"Skipping {title}: no image found.")
                continue
            img_url = img_meta.get("source")
            # Strip query params like ?utm_source...
            clean_url = img_url.split("?")[0]
            print(f"Downloading {title} from {clean_url}...")
            
            img_req = urllib.request.Request(clean_url, headers=HEADERS)
            with urllib.request.urlopen(img_req, timeout=25) as img_resp:
                raw_bytes = img_resp.read()
                
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                rgb_img = pil_img.convert("RGB")
                rgb_img.thumbnail((1600, 900), Image.Resampling.LANCZOS)
                rgb_img.save(target_path, "JPEG", quality=90)
                print(f"[OK] Saved {fname} ({os.path.getsize(target_path)} bytes, size={rgb_img.size})")
    except Exception as e:
        print(f"Error processing {title}: {e}")

print("Download step completed.")
