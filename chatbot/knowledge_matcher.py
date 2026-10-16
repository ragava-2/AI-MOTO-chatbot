import os
import re
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def normalize_text(text: str) -> str:
    """Normalizes query text by lowercasing, standardizing whitespace and punctuation."""
    if not text:
        return ""
    # Lowercase and replace dashes/underscores with spaces
    norm = text.lower()
    norm = re.sub(r'[-_/]', ' ', norm)
    # Remove excessive punctuation
    norm = re.sub(r'[^\w\s\d]', ' ', norm)
    # Collapse whitespace
    norm = re.sub(r'\s+', ' ', norm).strip()
    return norm

def extract_year(text: str) -> Optional[int]:
    """Extracts a 4-digit automotive model year (1900-2099) if present."""
    matches = re.findall(r'\b(19\d\d|20\d\d)\b', text)
    if matches:
        return int(matches[0])
    return None

def detect_vehicle_type(query_text: str = "", default_type: Optional[str] = None) -> str:
    """Detects expected vehicle type (bike or car) with user keyword precedence."""
    text = normalize_text(query_text)
    bike_terms = ["bike", "motorcycle", "scooter", "scooty", "two wheeler", "2 wheeler", "superbike", "cruiser", "moped"]
    car_terms = ["car", "automobile", "sedan", "suv", "hatchback", "four wheeler", "4 wheeler", "coupe", "convertible"]
    
    # Tamil terms
    if any(w in (query_text or "") for w in ["பைக்", "இருசக்கர"]):
        return "bike"
    if any(w in (query_text or "") for w in ["கார்", "மகிழுந்து"]):
        return "car"

    has_bike = any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in bike_terms)
    has_car = any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in car_terms)

    if has_bike and not has_car:
        return "bike"
    elif has_car and not has_bike:
        return "car"
    elif default_type in ["bike", "car"]:
        return default_type
    return "bike"

def get_all_manufacturers() -> List[str]:
    """Returns distinct manufacturers currently cataloged in the database."""
    from database.models import VehicleKnowledge
    from extensions import db
    try:
        results = db.session.query(VehicleKnowledge.manufacturer).distinct().all()
        return [r[0] for r in results]
    except Exception:
        # Fallback list if DB query fails
        return ["Yamaha", "Royal Enfield", "BMW", "Maruti Suzuki", "Honda", "Bajaj", "KTM", "Hyundai", "Tata"]

def match_manufacturer(query_text: str, vehicle_type: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Identifies manufacturer in query.
    Returns: (matched_manufacturer_or_None, unknown_manufacturer_or_None)
    """
    norm_q = normalize_text(query_text)
    known_manufacturers = get_all_manufacturers()
    
    # Check known manufacturers in DB
    for m in known_manufacturers:
        norm_m = normalize_text(m)
        if re.search(r'\b' + re.escape(norm_m) + r'\b', norm_q):
            return m, None
        # Support common manufacturer short names (e.g. Maruti, Suzuki, Enfield, RE)
        for part in norm_m.split():
            if len(part) >= 3 and re.search(r'\b' + re.escape(part) + r'\b', norm_q):
                return m, None

    # Check for known automotive brands not in our local database
    other_known_brands = [
        "ducati", "harley", "kawasaki", "tvs", "hero", "toyota", "audi",
        "mercedes", "porsche", "ford", "volkswagen", "mahindra", "kia", "nissan", "skoda"
    ]
    for b in other_known_brands:
        if re.search(r'\b' + re.escape(b) + r'\b', norm_q):
            return None, b.title()

    return None, None

class MatchResult(dict):
    """Dictionary subclass supporting both dot-access and bracket-access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

def match_exact_vehicle_knowledge(
    query_text: str,
    vehicle_type: Optional[str] = None,
    vehicle_context: Optional[str] = None
) -> MatchResult:
    """
    Executes 6-stage exact and safe matching:
    1. Input normalization
    2. Vehicle type match
    3. Manufacturer match
    4. Exact model match (Strict: similar models are rejected)
    5. Year range validation
    6. Component match & image validation
    """
    from database.models import VehicleKnowledge
    
    if vehicle_type is None and vehicle_context is not None:
        vehicle_type = vehicle_context

    norm_q = normalize_text(query_text)
    expected_v_type = detect_vehicle_type(query_text, default_type=vehicle_type)
    req_year = extract_year(query_text)
    
    result = MatchResult({
        "matched": False,
        "status": "unverified", # "exact_match", "unknown_manufacturer", "unknown_model", "year_mismatch", "unverified"
        "confidence": 0.0,
        "verified": False,
        "vehicle_type": expected_v_type,
        "manufacturer": None,
        "model": None,
        "year_requested": req_year,
        "year_range": None,
        "year_mismatch": False,
        "component_name": None,
        "specifications": {},
        "image_path": None,
        "is_placeholder": False,
        "placeholder_title": None,
        "placeholder_message": None,
        "message": ""
    })

    # Stage 2: Manufacturer matching
    matched_manuf, unknown_manuf = match_manufacturer(query_text, expected_v_type)
    
    if unknown_manuf:
        result["status"] = "unknown_manufacturer"
        result["manufacturer"] = unknown_manuf
        result["is_placeholder"] = True
        result["placeholder_title"] = f"Uncataloged Manufacturer: {unknown_manuf}"
        result["placeholder_message"] = (
            f"The manufacturer '{unknown_manuf}' is not currently cataloged in the local verified knowledge base. "
            "No unverified or guessed specifications can be provided."
        )
        return result

    if not matched_manuf:
        # No known manufacturer mentioned
        result["status"] = "no_manufacturer"
        return result

    result["manufacturer"] = matched_manuf

    # Stage 3: Exact Model Matching
    # Fetch all records under this manufacturer and vehicle type
    records = VehicleKnowledge.query.filter_by(
        vehicle_type=expected_v_type,
        manufacturer=matched_manuf
    ).all()

    if not records:
        # Manufacturer exists, but not for this vehicle type (e.g. BMW bike when DB only has BMW cars)
        result["status"] = "wrong_vehicle_type"
        result["is_placeholder"] = True
        result["placeholder_title"] = f"Verified {matched_manuf} {expected_v_type.capitalize()} Image Unavailable"
        result["placeholder_message"] = (
            f"The verified database contains {matched_manuf} cars, but no {matched_manuf} {expected_v_type} records. "
            f"Strict vehicle type validation prevented displaying an unrelated car image."
        )
        return result

    # Identify distinct models under this manufacturer
    model_groups = {}
    for r in records:
        if r.model not in model_groups:
            model_groups[r.model] = {
                "model": r.model,
                "model_aliases": r.model_aliases or [],
                "year_start": r.year_start,
                "year_end": r.year_end,
                "records": []
            }
        model_groups[r.model]["records"].append(r)

    matched_model_name = None
    for m_name, m_info in model_groups.items():
        candidates = [m_name] + m_info["model_aliases"]
        for c in candidates:
            norm_c = normalize_text(c)
            # Exact token boundary match
            if re.search(r'\b' + re.escape(norm_c) + r'\b', norm_q):
                matched_model_name = m_name
                break
        if matched_model_name:
            break

    # STRICT RULE 7: Do not treat a similar model as an exact match!
    # Check if user mentioned another distinct model/version (e.g. "R3", "R15 V3", "R15 V2", "Classic 500", "M3")
    manuf_low = matched_manuf.lower()
    if manuf_low == "yamaha":
        if re.search(r'\br3\b|\br15\s*v[123]\b|\bversion\s*[123]\b|\bmt\s*15\b|\bfz\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Model Rejected"
            result["placeholder_message"] = (
                "The requested model is not cataloged in the verified knowledge base. "
                "AI MOTO strictly rejects substituting a similar model (e.g., YZF-R15 V4) for an unverified model."
            )
            return result
    elif manuf_low == "bmw":
        if re.search(r'\bm3\b|\bm5\b|\bm2\b|\bs1000rr\b|\br1250\b|\bgs\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Model Rejected"
            result["placeholder_message"] = (
                "The requested BMW model is not cataloged in the verified knowledge base. "
                "Similar model substitution is strictly prohibited."
            )
            return result
    elif manuf_low == "honda":
        if re.search(r'\bdio\b|\bshine\b|\bunicorn\b|\bcbr\b|\bhornet\b|\bcb350\b|\bcity\b|\bcivic\b|\bamaze\b|\belevate\b|\bactiva\s*125\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Honda Model Rejected"
            result["placeholder_message"] = (
                "The requested Honda model is not cataloged. "
                "AI MOTO strictly rejects substituting a different model (e.g., Activa 6G) for an unverified model."
            )
            return result
    elif manuf_low == "bajaj":
        if re.search(r'\bpulsar\s*(220|ns200|rs200|250|n160|125)\b|\bdominar\b|\bplatina\b|\bavenger\b|\bct\s*100\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Bajaj Model Rejected"
            result["placeholder_message"] = (
                "The requested Bajaj model is not cataloged. "
                "AI MOTO strictly rejects substituting a different model (e.g., Pulsar 150) for an unverified model."
            )
            return result
    elif manuf_low == "ktm":
        if re.search(r'\brc\s*(390|200|125)\b|\bduke\s*(200|250|125|790|890|1290)\b|\badventure\s*390\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact KTM Model Rejected"
            result["placeholder_message"] = (
                "The requested KTM model is not cataloged. "
                "AI MOTO strictly rejects substituting a different model (e.g., Duke 390) for an unverified model."
            )
            return result
    elif manuf_low == "hyundai":
        if re.search(r'\bvenue\b|\bverna\b|\bi20\b|\bi10\b|\btucson\b|\balcazar\b|\bkona\b|\bioniq\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Hyundai Model Rejected"
            result["placeholder_message"] = (
                "The requested Hyundai model is not cataloged in the local knowledge base. "
                "Substituting a similar model (e.g., Creta) is strictly prohibited."
            )
            return result
    elif manuf_low == "tata":
        if re.search(r'\bharrier\b|\bsafari\b|\bpunch\b|\btiago\b|\btigor\b|\baltroz\b|\bcurvv\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Tata Model Rejected"
            result["placeholder_message"] = (
                "The requested Tata model is not cataloged in the local knowledge base. "
                "Substituting a similar model (e.g., Nexon) is strictly prohibited."
            )
            return result
    elif manuf_low == "royal enfield":
        if re.search(r'\bhunter\b|\bbullet\b|\bmeteor\b|\bhimalayan\b|\binterceptor\b|\bcontinental\b|\bclassic\s*500\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Royal Enfield Model Rejected"
            result["placeholder_message"] = (
                "The requested Royal Enfield model is not cataloged. "
                "AI MOTO strictly rejects substituting Classic 350 for an unverified model."
            )
            return result
    elif manuf_low == "maruti suzuki":
        if re.search(r'\bbaleno\b|\bbrezza\b|\bdzire\b|\bertiga\b|\bwagon\s*r\b|\balto\b|\bciaz\b|\bgrand\s*vitara\b', norm_q):
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = "Inexact Maruti Suzuki Model Rejected"
            result["placeholder_message"] = (
                "The requested Maruti Suzuki model is not cataloged. "
                "AI MOTO strictly rejects substituting Swift for an unverified model."
            )
            return result

    if not matched_model_name:
        # Check if the query is a general brand showcase request (e.g. "Show me a Yamaha bike image")
        # without naming an uncataloged model name
        generic_tokens = {
            "show", "me", "a", "an", "the", "give", "display", "image", "photo", "picture", 
            "pic", "specs", "specification", "specifications", "details", "info", "overview",
            "bike", "motorcycle", "car", "vehicle", "auto", "automobile", "please", "look", "like",
            "படம்", "காட்டு", "பைக்", "கார்", "வாகனம்"
        }
        manuf_tokens = set(normalize_text(matched_manuf).split())
        comp_tokens = set()
        for r in records:
            if r.component_name:
                comp_tokens.update(normalize_text(r.component_name).split())
                for ca in (r.component_aliases or []):
                    comp_tokens.update(normalize_text(ca).split())

        query_tokens = [w for w in re.findall(r'[a-zA-Z0-9\u0B80-\u0BFF]+', norm_q) if len(w) > 1]
        unmatched_tokens = [
            t for t in query_tokens 
            if t not in generic_tokens and t not in manuf_tokens and t not in comp_tokens
        ]

        if not unmatched_tokens and len(model_groups) == 1:
            # Single cataloged model for this brand and vehicle type (e.g. Yamaha R15 for Yamaha bike)
            matched_model_name = list(model_groups.keys())[0]
        else:
            # User named an uncataloged model (e.g. "Hunter", "Innova", "Scorpio")
            result["status"] = "unknown_model"
            result["confidence"] = 0.0
            result["is_placeholder"] = True
            result["placeholder_title"] = f"Uncataloged {matched_manuf} Model"
            result["placeholder_message"] = (
                f"The exact model requested for {matched_manuf} is not cataloged. "
                "Guessed or similar models are strictly not displayed."
            )
            return result

    result["model"] = matched_model_name
    model_data = model_groups[matched_model_name]
    result["year_range"] = (model_data["year_start"], model_data["year_end"])

    # Stage 4: Year Range Validation
    if req_year is not None:
        y_start = model_data["year_start"]
        y_end = model_data["year_end"]
        if (y_start and req_year < y_start) or (y_end and req_year > y_end):
            result["year_mismatch"] = True
            result["status"] = "year_mismatch"
            result["is_placeholder"] = True
            result["placeholder_title"] = f"Model Year Mismatch ({req_year})"
            result["placeholder_message"] = (
                f"The requested year {req_year} is outside the production range ({y_start} - {y_end or 'Present'}) "
                f"for the verified {matched_manuf} {matched_model_name}."
            )
            return result

    # Stage 5: Component Matching
    # Check if a component is queried
    model_records = model_data["records"]
    matched_comp_record = None
    
    for r in model_records:
        if r.component_name:
            candidates = [r.component_name] + (r.component_aliases or [])
            for c in candidates:
                norm_c = normalize_text(c)
                if re.search(r'\b' + re.escape(norm_c) + r'\b', norm_q):
                    matched_comp_record = r
                    break
        if matched_comp_record:
            break

    # If user explicitly asked for an uncataloged component (e.g. "Yamaha R15 turbocharger")
    if not matched_comp_record:
        uncataloged_parts = ["turbocharger", "supercharger", "carburetor", "intercooler", "nitrous"]
        for up in uncataloged_parts:
            if re.search(r'\b' + re.escape(up) + r'\b', norm_q):
                result["status"] = "unknown_component"
                result["component_name"] = up.title()
                result["is_placeholder"] = True
                result["placeholder_title"] = f"Unverified Component: {up.title()}"
                result["placeholder_message"] = (
                    f"The component '{up.title()}' is not a verified OEM component for {matched_manuf} {matched_model_name}. "
                    "Unverified compatibility information will not be invented."
                )
                return result

    # If matched a specific component
    if matched_comp_record:
        target_rec = matched_comp_record
        result["component_name"] = target_rec.component_name
    else:
        # Match model overview record (where component_name is null)
        overview_rec = next((r for r in model_records if r.component_name is None), None)
        target_rec = overview_rec or model_records[0]

    # Stage 6: Image Validation & Verified Flag
    result["matched"] = True
    result["confidence"] = float(target_rec.confidence)
    result["verified"] = bool(target_rec.verified)
    result["status"] = "exact_match"
    result["specifications"] = target_rec.specifications or {}

    # Image validation
    img_path = target_rec.image_path
    if img_path:
        clean_p = img_path.lstrip("/\\")
        disk_file = BASE_DIR / clean_p
        if disk_file.exists() and target_rec.verified:
            result["image_path"] = target_rec.image_path
            result["image_source"] = target_rec.image_source
            result["is_placeholder"] = False
        else:
            # File does not exist on disk or record marked unverified
            result["image_path"] = None
            result["is_placeholder"] = True
            result["placeholder_title"] = f"Verified Image Unavailable ({target_rec.model})"
            result["placeholder_message"] = (
                f"An approved verified image for {target_rec.manufacturer} {target_rec.model} "
                f"{'(' + target_rec.component_name + ')' if target_rec.component_name else ''} is currently unavailable. "
                "Images from other models are strictly not displayed."
            )
    else:
        # No image cataloged for this model/component (e.g. Swift overview)
        result["image_path"] = None
        result["is_placeholder"] = True
        result["placeholder_title"] = f"Verified Image Unavailable ({target_rec.model})"
        result["placeholder_message"] = (
            f"No verified image is currently cataloged for {target_rec.manufacturer} {target_rec.model}. "
            "Images from other models are strictly suppressed."
        )

    return result
