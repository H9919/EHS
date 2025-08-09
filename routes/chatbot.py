# routes/chatbot.py - Enhanced version with better debugging and error handling
import json
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template

chatbot_bp = Blueprint("chatbot", __name__)

# Lazy loading of chatbot to save memory
_chatbot_instance = None
CHATBOT_AVAILABLE = False

def get_chatbot():
    """Lazy load chatbot only when needed"""
    global _chatbot_instance, CHATBOT_AVAILABLE
    
    if _chatbot_instance is None:
        try:
            # Try to import the memory-optimized version first
            from services.ehs_chatbot import create_chatbot
            _chatbot_instance = create_chatbot()
            CHATBOT_AVAILABLE = _chatbot_instance is not None
            if CHATBOT_AVAILABLE:
                print("✓ Memory-optimized chatbot loaded successfully")
            else:
                print("⚠ Chatbot creation returned None")
        except Exception as e:
            print(f"⚠ Chatbot loading error: {e}")
            import traceback
            traceback.print_exc()
            CHATBOT_AVAILABLE = False
            _chatbot_instance = None
    
    return _chatbot_instance

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = Path("static/uploads")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    """Memory-efficient chat interface with extensive debugging"""
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    debug_info = {
        "timestamp": time.time(),
        "method": request.method,
        "content_type": request.content_type,
        "has_json": request.is_json,
        "has_form": bool(request.form),
        "has_files": bool(request.files),
        "chatbot_available": CHATBOT_AVAILABLE
    }
    
    try:
        # Parse request data efficiently with debugging
        user_message, user_id, context, uploaded_file = parse_request_data()
        
        debug_info.update({
            "user_message": user_message[:100] if user_message else None,
            "user_id": user_id,
            "context_keys": list(context.keys()) if context else [],
            "has_uploaded_file": bool(uploaded_file),
            "file_info": uploaded_file.get("filename") if uploaded_file else None
        })
        
        print(f"DEBUG: Chat request - {debug_info}")
        
        # Get chatbot instance (lazy loaded)
        chatbot = get_chatbot()
        
        if chatbot:
            try:
                print(f"DEBUG: Processing with chatbot - message: '{user_message}', context: {context}")
                
                # Store current state for debugging
                pre_state = {
                    "mode": getattr(chatbot, 'current_mode', 'unknown'),
                    "context": dict(getattr(chatbot, 'current_context', {})),
                    "slot_state": dict(getattr(chatbot, 'slot_filling_state', {}))
                }
                
                response = chatbot.process_message(user_message, user_id, context)
                
                # Store post state for debugging
                post_state = {
                    "mode": getattr(chatbot, 'current_mode', 'unknown'),
                    "context": dict(getattr(chatbot, 'current_context', {})),
                    "slot_state": dict(getattr(chatbot, 'slot_filling_state', {}))
                }
                
                # Add comprehensive debugging information
                response["debug_info"] = {
                    "request_debug": debug_info,
                    "pre_processing_state": pre_state,
                    "post_processing_state": post_state,
                    "state_changed": pre_state != post_state,
                    "response_type": response.get("type", "unknown"),
                    "processing_successful": True
                }
                
                print(f"DEBUG: Response generated successfully: {response.get('type', 'unknown')}")
                print(f"DEBUG: State change: {pre_state} -> {post_state}")
                
                return jsonify(response)
                
            except Exception as e:
                print(f"ERROR: Chatbot processing failed: {e}")
                import traceback
                error_traceback = traceback.format_exc()
                print(error_traceback)
                
                # Return enhanced fallback with full debugging info
                return jsonify(get_enhanced_fallback_with_debug(
                    user_message, uploaded_file, str(e), debug_info, error_traceback
                ))
        else:
            print("WARNING: Chatbot not available, using fallback")
            # Lightweight fallback without heavy imports
            return jsonify(get_lightweight_fallback_response(user_message, uploaded_file, debug_info))
            
    except Exception as e:
        print(f"ERROR: Chat route exception: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        print(error_traceback)
        
        return jsonify({
            "message": "I'm having trouble processing your request. Let me direct you to the right place.",
            "type": "error",
            "actions": [
                {
                    "text": "📝 Report Incident Directly",
                    "action": "navigate",
                    "url": "/incidents/new"
                },
                {
                    "text": "🛡️ Safety Concern Form",
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📊 Dashboard",
                    "action": "navigate", 
                    "url": "/dashboard"
                }
            ],
            "debug_info": {
                "error": str(e),
                "traceback": error_traceback if os.getenv("FLASK_ENV") == "development" else None,
                "request_info": debug_info
            }
        })

def parse_request_data():
    """Efficiently parse request data with detailed debugging"""
    try:
        print(f"DEBUG: Parsing request - Content-Type: {request.content_type}")
        print(f"DEBUG: Is JSON: {request.is_json}")
        print(f"DEBUG: Form data: {dict(request.form)}")
        print(f"DEBUG: Files: {list(request.files.keys())}")
        
        if request.is_json:
            data = request.get_json()
            user_message = data.get("message", "")
            user_id = data.get("user_id", "default_user")
            context = data.get("context", {})
            uploaded_file = None
            print(f"DEBUG: JSON data parsed - message: '{user_message}', context: {context}")
        else:
            user_message = request.form.get("message", "")
            user_id = request.form.get("user_id", "default_user")
            context = {}
            
            print(f"DEBUG: Form data parsed - message: '{user_message}'")
            
            # Handle file upload
            uploaded_file = None
            if 'file' in request.files:
                file = request.files['file']
                print(f"DEBUG: File upload detected - filename: {file.filename}, type: {file.content_type}")
                if file and file.filename and allowed_file(file.filename):
                    uploaded_file = handle_file_upload_efficient(file)
                    print(f"DEBUG: File processed successfully: {uploaded_file}")
                else:
                    print("DEBUG: File rejected - invalid filename or type")
        
        # Update context with file info if present
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            if not user_message.strip():
                user_message = f"I've uploaded a file ({uploaded_file['filename']})"
                print(f"DEBUG: Generated message for file upload: '{user_message}'")
        
        return user_message, user_id, context, uploaded_file
        
    except Exception as e:
        print(f"ERROR: Failed to parse request data: {e}")
        import traceback
        traceback.print_exc()
        return "", "default_user", {}, None

def handle_file_upload_efficient(file):
    """Handle file upload with minimal memory usage and debugging"""
    try:
        ensure_upload_dir()
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        file_path = UPLOAD_FOLDER / unique_filename
        
        print(f"DEBUG: Saving file to {file_path}")
        
        # Save file
        file.save(file_path)
        
        file_info = {
            "filename": filename,
            "path": str(file_path),
            "type": file.content_type or "application/octet-stream",
            "size": os.path.getsize(file_path)
        }
        
        print(f"DEBUG: File saved successfully: {file_info}")
        return file_info
        
    except Exception as e:
        print(f"ERROR: File upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_enhanced_fallback_with_debug(message, uploaded_file=None, error_msg="", debug_info=None, traceback_str=""):
    """Enhanced fallback with comprehensive debugging information"""
    message_lower = message.lower() if message else ""
    
    # Smart fallback based on message content
    if any(word in message_lower for word in ["injured", "injury", "hurt", "medical"]):
        return {
            "message": "🚨 **I understand someone was injured.**\n\nLet me direct you to our injury incident reporting form to ensure all details are captured properly.",
            "type": "injury_incident_direct",
            "actions": [
                {
                    "text": "🩹 Report Injury Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=injury"
                },
                {
                    "text": "🚑 Emergency Procedures",
                    "action": "navigate",
                    "url": "/procedures/emergency"
                }
            ],
            "guidance": "**Remember:** If medical attention is needed, call 911 first. Report to the system after ensuring the person's safety.",
            "debug_info": {
                "fallback_reason": "injury_detected",
                "original_message": message,
                "error": error_msg,
                "request_debug": debug_info,
                "traceback": traceback_str if os.getenv("FLASK_ENV") == "development" else None
            }
        }
    
    elif any(word in message_lower for word in ["workplace.*injury", "involves.*injury"]):
        return {
            "message": "🩹 **I understand this involves a workplace injury.**\n\nLet me guide you through our injury incident reporting process.",
            "type": "workplace_injury_direct",
            "actions": [
                {
                    "text": "🩹 Start Injury Report",
                    "action": "navigate",
                    "url": "/incidents/new?type=injury"
                }
            ],
            "debug_info": {
                "fallback_reason": "workplace_injury_detected",
                "original_message": message,
                "error": error_msg,
                "request_debug": debug_info
            }
        }
    
    elif any(word in message_lower for word in ["vehicle", "car", "truck", "collision", "crash"]):
        return {
            "message": "🚗 **I understand this involves a vehicle incident.**\n\nLet me direct you to our vehicle incident reporting form.",
            "type": "vehicle_incident_direct",
            "actions": [
                {
                    "text": "🚗 Report Vehicle Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=vehicle"
                }
            ],
            "debug_info": {
                "fallback_reason": "vehicle_detected",
                "original_message": message,
                "error": error_msg
            }
        }
    
    elif any(word in message_lower for word in ["spill", "chemical", "leak", "environmental"]):
        return {
            "message": "🌊 **I understand this involves a chemical spill or environmental incident.**\n\nLet me direct you to our environmental incident reporting form.",
            "type": "environmental_incident_direct",
            "actions": [
                {
                    "text": "🌊 Report Environmental Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=environmental"
                }
            ],
            "debug_info": {
                "fallback_reason": "environmental_detected",
                "original_message": message,
                "error": error_msg
            }
        }
    
    # Default enhanced fallback
    return get_lightweight_fallback_response(message, uploaded_file, debug_info)

def get_lightweight_fallback_response(message, uploaded_file=None, debug_info=None):
    """Lightweight fallback responses without heavy processing"""
    message_lower = message.lower() if message else ""
    
    # Handle file uploads
    if uploaded_file:
        filename = uploaded_file.get("filename", "")
        file_type = uploaded_file.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this for incident reporting or safety documentation.",
                "type": "file_upload",
                "actions": [
                    {"text": "🚨 Report Incident", "action": "navigate", "url": "/incidents/new"},
                    {"text": "🛡️ Safety Concern", "action": "navigate", "url": "/safety-concerns/new"}
                ],
                "debug_info": debug_info
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis
