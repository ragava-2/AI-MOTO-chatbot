from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import base64
from werkzeug.utils import secure_filename
from extensions import db, bcrypt
from database.models import User, Conversation, ChatHistory
from chatbot.model import generate_ai_response, client as groq_client
import tempfile
import os
from datetime import datetime, timedelta

from sqlalchemy import func
import json
import re

chatbot_bp = Blueprint('chatbot', __name__)

def extract_structured_response(ai_raw_text, vision_data=None, query_text="", vehicle_type=None):
    """
    Safely extracts structured JSON vehicle/part cards from AI response text.
    Enriches with verified local automotive catalog images, pricing estimates,
    diagnostic checks, and safety guidance while strictly stripping hallucinated URLs.
    Returns: (clean_markdown_text, structured_dict_or_None)
    """
    if not ai_raw_text:
        return "", None

    structured_data = None
    clean_text = ai_raw_text

    # 1. Try explicit delimiter <<<STRUCTURED_JSON>>> ... <<<END_STRUCTURED_JSON>>>
    delimiter_pattern = r'<<<STRUCTURED_JSON>>>([\s\S]*?)<<<END_STRUCTURED_JSON>>>'
    match = re.search(delimiter_pattern, ai_raw_text)
    if match:
        json_str = match.group(1).strip()
        try:
            structured_data = json.loads(json_str)
            clean_text = re.sub(delimiter_pattern, '', ai_raw_text).strip()
        except Exception as e:
            print(f"[Structured Extract Warning] Failed to parse delimited JSON: {e}")

    # 2. If not found, try markdown code block ```json ... ```
    if not structured_data:
        codeblock_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
        match = re.search(codeblock_pattern, ai_raw_text)
        if match:
            json_str = match.group(1).strip()
            try:
                candidate = json.loads(json_str)
                if isinstance(candidate, dict) and 'response_type' in candidate:
                    structured_data = candidate
                    clean_text = re.sub(codeblock_pattern, '', ai_raw_text).strip()
            except Exception:
                pass

    # 3. If raw text is pure JSON
    if not structured_data and ai_raw_text.strip().startswith('{') and ai_raw_text.strip().endswith('}'):
        try:
            candidate = json.loads(ai_raw_text.strip())
            if isinstance(candidate, dict) and 'response_type' in candidate:
                structured_data = candidate
                clean_text = candidate.get('summary') or candidate.get('problem_summary') or ""
        except Exception:
            pass

    # If clean_text became empty, fallback to summary or title from structured data
    if not clean_text and structured_data:
        clean_text = structured_data.get('summary') or structured_data.get('problem_summary') or structured_data.get('title') or ""

    # Sanitize and enhance with vision detection if present
    if structured_data and isinstance(structured_data, dict):
        if vision_data and vision_data.get("detected"):
            knowledge = vision_data.get("knowledge") or {}
            structured_data["vision_detection"] = {
                "detected": True,
                "part_class": vision_data.get("part_class"),
                "part_name": knowledge.get("name") or vision_data.get("part_class"),
                "category": knowledge.get("category", "Automotive Component"),
                "confidence": round(float(vision_data.get("confidence", 0.0)) * 100, 1),
                "bbox": vision_data.get("bbox"),
                "knowledge": knowledge
            }
    elif vision_data and vision_data.get("detected"):
        # If model didn't return JSON but YOLO detected a part, create a vision diagnostic card!
        knowledge = vision_data.get("knowledge") or {}
        part_name = knowledge.get("name") or vision_data.get("part_class", "Vehicle Part")
        structured_data = {
            "response_type": "diagnostic_result",
            "title": f"Computer Vision Part Inspection: {part_name}",
            "category": knowledge.get("category", "Automotive Component"),
            "summary": f"Detected {part_name} with {round(float(vision_data.get('confidence', 0.0)) * 100, 1)}% confidence.",
            "components": [
                {
                    "name": part_name,
                    "category": knowledge.get("category", "Automotive Component"),
                    "purpose": knowledge.get("function", "Critical vehicle component"),
                    "working": knowledge.get("working", "Operates in vehicle powertrain or chassis."),
                    "symptoms": knowledge.get("common_problems", []),
                    "checks": knowledge.get("maintenance", []),
                    "safety_warning": "Ensure vehicle is turned off and cool before physically inspecting components."
                }
            ],
            "vision_detection": {
                "detected": True,
                "part_class": vision_data.get("part_class"),
                "part_name": part_name,
                "category": knowledge.get("category", "Automotive Component"),
                "confidence": round(float(vision_data.get("confidence", 0.0)) * 100, 1),
                "bbox": vision_data.get("bbox"),
                "knowledge": knowledge
            },
            "related_questions": [
                f"How often should the {part_name.lower()} be serviced?",
                f"What are the warning signs that a {part_name.lower()} is failing?",
                f"Can I replace the {part_name.lower()} myself?"
            ]
        }

    # Anti-hallucination sanitization: strip any fake image URLs generated by LLM
    try:
        from chatbot.image_retriever import sanitize_ai_text, enrich_structured_card
        clean_text = sanitize_ai_text(clean_text or "")
        structured_data = enrich_structured_card(
            structured_data,
            query_text=query_text or "",
            vehicle_type=vehicle_type
        )
    except Exception as e:
        print(f"[ImageRetriever Warning] Enrichment failed: {e}")

    # If the LLM output was a refusal or empty, but we have a valid vehicle/component card, provide clear text
    if structured_data:
        if "I am AI MOTO, an AI vehicle assistant" in (clean_text or "") or not (clean_text or "").strip():
            if structured_data.get("is_placeholder"):
                clean_text = structured_data.get("placeholder_message") or "Verified image not available in local catalog."
            elif structured_data.get("title"):
                clean_text = f"Here is the verified visual overview and technical specifications for the **{structured_data.get('title')}**."

    return clean_text or ai_raw_text, structured_data

@chatbot_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"message": "Please provide username, email, and password."}), 400
        
    # Case-insensitive duplicate checks
    if User.query.filter(func.lower(User.username) == username.lower()).first():
        print(f"[AUTH DIAGNOSTIC] Registration for '{username}': Username already registered.", flush=True)
        return jsonify({"message": "Username is already registered. Please log in or choose a different username."}), 400
        
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        print(f"[AUTH DIAGNOSTIC] Registration for '{email}': Email already registered.", flush=True)
        return jsonify({"message": "Email is already registered. Please log in or use a different email."}), 400
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        print(f"[AUTH DIAGNOSTIC] Registration SUCCEEDED: user '{username}' (id={new_user.id}) created.", flush=True)

        # Automatically issue 7-day JWT access token so user is logged in instantly
        access_token = create_access_token(
            identity=str(new_user.id),
            expires_delta=timedelta(days=7)
        )
        return jsonify({
            "message": "User registered and logged in successfully!",
            "access_token": access_token,
            "username": new_user.username,
            "email": new_user.email,
            "user_id": new_user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"[AUTH DIAGNOSTIC] Registration error: {repr(e)}", flush=True)
        return jsonify({"message": "Registration failed due to a database error."}), 500

@chatbot_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = (data.get('username') or '').strip()
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({"message": "Please enter username and password."}), 400
        
    # Case-insensitive match on both username and email
    clean_identifier = identifier.lower()
    user = User.query.filter(
        (func.lower(User.username) == clean_identifier) | 
        (func.lower(User.email) == clean_identifier)
    ).first()
    
    if not user:
        print(f"[AUTH DIAGNOSTIC] Login for '{identifier}': User NOT FOUND in database.", flush=True)
        return jsonify({
            "message": f"Account '{identifier}' does not exist yet. Please click 'Register' to create this account.",
            "user_not_found": True
        }), 401

    print(f"[AUTH DIAGNOSTIC] Login for '{identifier}': User FOUND in database.", flush=True)

    if bcrypt.check_password_hash(user.password, password):
        print(f"[AUTH DIAGNOSTIC] Login for '{identifier}': Password verification SUCCEEDED.", flush=True)
        # 7-day token expiration
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        return jsonify({
            "access_token": access_token,
            "username": user.username,
            "email": user.email,
            "user_id": user.id
        }), 200
    else:
        print(f"[AUTH DIAGNOSTIC] Login for '{identifier}': Password verification FAILED.", flush=True)
        return jsonify({"message": "Incorrect password. Please try again."}), 401

@chatbot_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found."}), 404
        
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200

@chatbot_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    current_user_id = get_jwt_identity()
    user_message = (request.form.get('message') or "").strip()
    conversation_id = request.form.get('conversation_id')
    vehicle_type = (request.form.get('vehicle_type') or "bike").lower().strip()
    language = request.form.get('language', "English").strip()
    mode = request.form.get('mode', "chat").strip()
    file = request.files.get('file')
    
    if not user_message and not file:
        return jsonify({"message": "Please enter a question or upload an image."}), 400
        
    base64_image = None
    filename_str = ""
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        filename_str = filename
        if '.' not in filename:
            return jsonify({"message": "Please upload a valid JPG, JPEG, PNG, or WEBP image."}), 400
            
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            return jsonify({"message": "Please upload a valid JPG, JPEG, PNG, or WEBP image."}), 400
            
        file_bytes = file.read()
        if len(file_bytes) == 0:
            return jsonify({"message": "Uploaded image file is empty."}), 400
            
        # 5MB size limit
        if len(file_bytes) > 5 * 1024 * 1024:
            return jsonify({"message": "Image size is too large. Please upload a smaller image."}), 400
            
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
            
    # Resolve or create Conversation
    if conversation_id:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user_id).first()
        if not conversation:
            return jsonify({"message": "Conversation not found."}), 404
        vehicle_type = conversation.vehicle_type or vehicle_type
        conversation.updated_at = datetime.utcnow()
    else:
        # Generate friendly title
        if user_message:
            title_text = user_message[:45] + ("..." if len(user_message) > 45 else "")
        else:
            title_text = f"{vehicle_type.capitalize()} Image Analysis"
            
        conversation = Conversation(
            title=title_text,
            vehicle_type=vehicle_type if vehicle_type in ['bike', 'car'] else 'bike',
            user_id=current_user_id
        )
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
            
    try:
        ai_response = generate_ai_response(
            question=user_message,
            conversation_id=conversation.id,
            base64_image=base64_image,
            vehicle_type=conversation.vehicle_type,
            language=language,
            mode=mode
        )
    except Exception as e:
        print("\n[Chat Route Exception]:", repr(e), flush=True)
        return jsonify({
            "message": "An error occurred while communicating with the AI service. Please try again.",
            "error": str(e)
        }), 500
        
    display_msg = user_message
    if filename_str:
        display_msg = f"[Attached: {filename_str}]\n{display_msg}".strip()

    # Run computer vision detection if image was uploaded
    vision_data = None
    if base64_image:
        try:
            from chatbot.detector import detect_vehicle_part
            vision_data = detect_vehicle_part(base64_image, conf_threshold=0.25)
        except Exception as e:
            print(f"[Vision Route Warning] Detection failed: {e}")

    # Extract clean text and structured payload safely with verified image matching
    clean_display_text, structured_obj = extract_structured_response(
        ai_response,
        vision_data=vision_data,
        query_text=user_message,
        vehicle_type=conversation.vehicle_type
    )
        
    chat_history = ChatHistory(
        message=display_msg,
        response=ai_response,
        conversation_id=conversation.id
    )
    db.session.add(chat_history)
    db.session.commit()
    
    return jsonify({
        "message": display_msg, 
        "response": clean_display_text,
        "structured": structured_obj,
        "conversation_id": conversation.id,
        "vehicle_type": conversation.vehicle_type,
        "title": conversation.title
    }), 200

@chatbot_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    current_user_id = get_jwt_identity()
    query_str = request.args.get('q', '').strip().lower()
    
    conversations = Conversation.query.filter_by(user_id=current_user_id).order_by(Conversation.updated_at.desc()).all()
    
    conv_list = []
    for c in conversations:
        # Check title or message match if search query present
        if query_str:
            title_matches = query_str in c.title.lower()
            msg_matches = any(query_str in m.message.lower() or query_str in m.response.lower() for m in c.messages)
            if not (title_matches or msg_matches):
                continue
                
        conv_list.append({
            "id": c.id,
            "title": c.title,
            "vehicle_type": c.vehicle_type or "bike",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "message_count": len(c.messages)
        })
        
    return jsonify({"conversations": conv_list}), 200

@chatbot_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_history(conversation_id):
    current_user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user_id).first()
    
    if not conversation:
        return jsonify({"message": "Conversation not found."}), 404
        
    history = ChatHistory.query.filter_by(conversation_id=conversation_id).order_by(ChatHistory.timestamp.asc()).all()
    
    history_list = []
    for h in history:
        clean_text, structured_obj = extract_structured_response(
            h.response,
            query_text=h.message,
            vehicle_type=conversation.vehicle_type
        )
        history_list.append({
            "id": h.id,
            "message": h.message,
            "response": clean_text,
            "structured": structured_obj,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        })
        
    return jsonify({
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "vehicle_type": conversation.vehicle_type or "bike",
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        },
        "history": history_list
    }), 200

@chatbot_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    current_user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user_id).first()
    
    if not conversation:
        return jsonify({"message": "Conversation not found."}), 404
        
    try:
        db.session.delete(conversation)
        db.session.commit()
        return jsonify({"message": "Conversation deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        print("Delete error:", repr(e))
        return jsonify({"message": "Failed to delete conversation."}), 500

@chatbot_bp.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe_audio():
    if not groq_client:
        return jsonify({"message": "Groq client is not configured."}), 500
        
    if 'audio' not in request.files:
        return jsonify({"message": "No audio file provided."}), 400
        
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"message": "Empty audio file."}), 400
        
    language = request.form.get('language', 'English')
    vehicle_type = request.form.get('vehicle_type', 'bike')
    
    prompt = f"The user is asking about {vehicle_type} maintenance and problems."
    if language == 'Tamil':
        prompt = f"பைக்குகள் மற்றும் கார்கள் பற்றிய பயனர் குரல் பதிவு."
        
    temp_path = None
    try:
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(audio_file.filename or "recording.webm")
        temp_path = os.path.join(temp_dir, f"ai_moto_{os.getpid()}_{filename}")
        audio_file.save(temp_path)
        
        with open(temp_path, "rb") as file_handle:
            transcription = groq_client.audio.transcriptions.create(
                file=(filename, file_handle.read()),
                model="whisper-large-v3",
                prompt=prompt,
                response_format="json"
            )
            
        return jsonify({"text": transcription.text.strip()}), 200
        
    except Exception as e:
        print("\n[Transcription Error]:", repr(e), flush=True)
        return jsonify({"message": "Failed to transcribe audio.", "error": str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
