import os
import sys
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app
from extensions import db
from database.models import VehicleKnowledge

REQUIRED_FIELDS = ["vehicle_type", "manufacturer", "model"]
VALID_VEHICLE_TYPES = ["bike", "car"]

def validate_record(record, index, static_dir):
    """Validates schema, fields, and image existence for a record."""
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"Row {index}: Missing required field '{field}'.")
            
    v_type = str(record.get("vehicle_type", "")).lower().strip()
    if v_type not in VALID_VEHICLE_TYPES:
        errors.append(f"Row {index}: Invalid vehicle_type '{v_type}'. Must be 'bike' or 'car'.")
        
    # Check image path if provided
    img_path = record.get("image_path")
    verified_flag = bool(record.get("verified", True))
    
    if img_path:
        # Resolve absolute disk path
        clean_path = img_path.lstrip("/\\")
        disk_path = BASE_DIR / clean_path
        if not disk_path.exists():
            # Mark unverified if file missing
            verified_flag = False
            
    return errors, verified_flag

def import_catalog(catalog_path, force=False, dry_run=False):
    print("==========================================================")
    print("  AI MOTO: VEHICLE KNOWLEDGE DATABASE IMPORT UTILITY       ")
    print("==========================================================")
    print(f"Catalog File: {catalog_path}")
    print(f"Dry Run Mode: {dry_run}")
    
    if not os.path.exists(catalog_path):
        print(f"[ERROR] Catalog file not found at: {catalog_path}")
        return False
        
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON formatting in catalog: {e}")
        return False
        
    if not isinstance(data, list):
        print("[ERROR] Catalog JSON root must be a list of records.")
        return False
        
    print(f"Loaded {len(data)} records from catalog. Validating...")
    
    static_dir = BASE_DIR / "static"
    validation_errors = []
    validated_records = []
    
    for idx, rec in enumerate(data, start=1):
        errs, is_verified = validate_record(rec, idx, static_dir)
        if errs:
            validation_errors.extend(errs)
        else:
            rec_copy = dict(rec)
            rec_copy["verified"] = is_verified
            validated_records.append(rec_copy)
            
    if validation_errors:
        print("\n[VALIDATION FAILED] Please fix the following schema errors:")
        for err in validation_errors:
            print(f"  - {err}")
        return False
        
    print(f"✓ All {len(validated_records)} records successfully validated.")
    
    with app.app_context():
        # Ensure table exists
        db.create_all()
        
        # Check existing records in database to manage duplicates
        existing_count = VehicleKnowledge.query.count()
        print(f"Existing Vehicle Knowledge records in database: {existing_count}")
        
        should_update = force
        if existing_count > 0 and not force and not dry_run:
            ans = input("Existing records detected. Overwrite / update matching records? [y/N]: ").strip().lower()
            if ans in ['y', 'yes']:
                should_update = True
            else:
                print("Proceeding in append-only mode (duplicates will be skipped).")
                
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        verified_images = 0
        unverified_images = 0
        
        for rec in validated_records:
            v_type = rec["vehicle_type"].lower().strip()
            manuf = rec["manufacturer"].strip()
            model = rec["model"].strip()
            comp_name = rec.get("component_name")
            comp_name_clean = comp_name.strip() if comp_name else None
            
            # Check duplicate by (vehicle_type, manufacturer, model, component_name)
            existing = VehicleKnowledge.query.filter_by(
                vehicle_type=v_type,
                manufacturer=manuf,
                model=model,
                component_name=comp_name_clean
            ).first()
            
            if rec.get("verified"):
                verified_images += 1
            else:
                unverified_images += 1
                
            if existing:
                if should_update and not dry_run:
                    existing.model_aliases = rec.get("model_aliases", [])
                    existing.year_start = rec.get("year_start")
                    existing.year_end = rec.get("year_end")
                    existing.component_aliases = rec.get("component_aliases", [])
                    existing.specifications = rec.get("specifications", {})
                    existing.image_path = rec.get("image_path")
                    existing.image_source = rec.get("image_source", "local_verified")
                    existing.verified = rec.get("verified", True)
                    existing.confidence = float(rec.get("confidence", 1.0))
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                if not dry_run:
                    new_item = VehicleKnowledge(
                        vehicle_type=v_type,
                        manufacturer=manuf,
                        model=model,
                        model_aliases=rec.get("model_aliases", []),
                        year_start=rec.get("year_start"),
                        year_end=rec.get("year_end"),
                        component_name=comp_name_clean,
                        component_aliases=rec.get("component_aliases", []),
                        specifications=rec.get("specifications", {}),
                        image_path=rec.get("image_path"),
                        image_source=rec.get("image_source", "local_verified"),
                        verified=rec.get("verified", True),
                        confidence=float(rec.get("confidence", 1.0))
                    )
                    db.session.add(new_item)
                inserted_count += 1
                
        if not dry_run:
            db.session.commit()
            print("\n✓ Database commit complete.")
        else:
            print("\n✓ Dry-run completed. No database changes written.")
            
        print("\n==========================================================")
        print("                 IMPORT SUMMARY                           ")
        print("==========================================================")
        print(f"Total Validated in File  : {len(validated_records)}")
        print(f"New Records Inserted     : {inserted_count}")
        print(f"Existing Records Updated : {updated_count}")
        print(f"Duplicate Records Skipped: {skipped_count}")
        print(f"Verified Image Records   : {verified_images}")
        print(f"Unverified Image Records : {unverified_images}")
        print(f"Total Database Rows Now  : {VehicleKnowledge.query.count()}")
        print("==========================================================\n")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import vehicle knowledge data into SQLite database.")
    parser.add_argument("--file", default=str(BASE_DIR / "data" / "vehicle_knowledge_catalog.json"), help="Path to JSON catalog")
    parser.add_argument("--force", action="store_true", help="Automatically confirm overwrite of existing records")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing to database")
    args = parser.parse_args()
    
    success = import_catalog(args.file, force=args.force, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
