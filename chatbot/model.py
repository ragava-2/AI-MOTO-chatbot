import os
from groq import Groq
from dotenv import load_dotenv
from chatbot.memory import get_conversation_context
from chatbot.prompt import get_system_prompt
from chatbot.detector import detect_vehicle_part

# Load env variables
load_dotenv(override=True)

# Initialize Groq client with GROQ_API_KEY
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generate_ai_response(question, conversation_id=None, base64_image=None, vehicle_type="bike", language="English", mode="chat"):
    if not api_key or not client:
        raise ValueError("GROQ_API_KEY is not configured in .env file.")
        
    system_prompt = get_system_prompt(vehicle_type=vehicle_type, language=language, mode=mode)
    
    # Run YOLO11n Computer Vision Detection & Knowledge Lookup if image is provided
    if base64_image:
        detection = detect_vehicle_part(base64_image, conf_threshold=0.30)
        if detection.get("detected") and detection.get("prompt_context"):
            system_prompt += detection["prompt_context"]

    # Phase 2 Exact Knowledge Database Grounding
    if question:
        try:
            from chatbot.knowledge_matcher import match_exact_vehicle_knowledge
            kb_match = match_exact_vehicle_knowledge(question, vehicle_type=vehicle_type)
            if kb_match and kb_match.get("status") == "exact_match":
                kb_context = (
                    f"\n\n[VERIFIED DATABASE KNOWLEDGE (Confidence: {kb_match.get('confidence', 1.0)*100:.0f}%)]:\n"
                    f"- Manufacturer: {kb_match.get('manufacturer')}\n"
                    f"- Exact Model: {kb_match.get('model')}\n"
                )
                if kb_match.get("component_name"):
                    kb_context += f"- Component: {kb_match.get('component_name')}\n"
                if kb_match.get("specifications"):
                    kb_context += "- Verified Specifications:\n"
                    for k, v in kb_match["specifications"].items():
                        kb_context += f"  * {k}: {v}\n"
                if kb_match.get("image_path"):
                    kb_context += f"- Verified Local Image: Available ({kb_match.get('image_path')})\n"
                else:
                    kb_context += "- Verified Local Image: None (Placeholder active)\n"
                kb_context += "RULE: Ground your explanation directly on these verified database specifications. Do not fabricate alternative specs or prices."
                system_prompt += kb_context
            elif kb_match and kb_match.get("status") in ["unknown_model", "unknown_manufacturer", "year_mismatch", "wrong_vehicle_type", "unknown_component"]:
                warn_context = (
                    f"\n\n[DATABASE MATCH STATUS: {kb_match.get('status').upper()}]:\n"
                    f"- Advisory: {kb_match.get('placeholder_message')}\n"
                    "RULE: Explicitly notify the user about this unverified or mismatched model/component status. Do not invent false compatibility or specs."
                )
                system_prompt += warn_context
        except Exception as e:
            print(f"[Model Info] Knowledge grounding deferred: {e}")

    messages = [{"role": "system", "content": system_prompt}]
    
    # Fetch Conversation History if conversation_id provided
    if conversation_id:
        memory = get_conversation_context(conversation_id, limit=8)
        messages.extend(memory)
        
    # Handle multimodal (image upload) vs text
    if base64_image:
        user_content = [
            {"type": "text", "text": question or f"Please inspect this {vehicle_type} component and describe what is visible."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        messages.append({"role": "user", "content": user_content})
    elif question:
        messages.append({"role": "user", "content": question})
    else:
        return "Please ask a question."
        
    candidate_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None

    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=800,
                temperature=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            print(f"[Model Warning] Call to {model_name} failed: {e}. Trying fallback if available...", flush=True)

    print("\n========== GROQ API ERROR ==========")
    print("ERROR TYPE:", type(last_error).__name__)
    print("ERROR:", str(last_error))
    print("Full Error:", repr(last_error))
    print("====================================\n", flush=True)
    raise last_error
