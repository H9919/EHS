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
                "message": f"📄 **PDF received: {filename}**\n\nThis could be a Safety Data Sheet or documentation.",
                "type": "file_upload",
                "actions": [
                    {"text": "📋 Add to SDS Library", "action": "navigate", "url": "/sds/upload"}
                ],
                "debug_info": debug_info
            }
    
    # Enhanced keyword-based responses
    if any(word in message_lower for word in ["incident", "accident", "injury", "hurt", "damage", "spill", "report"]):
        return {
            "message": "🚨 **I'll help you report this incident.**\n\nTo ensure we capture all necessary details, please choose the type of incident:",
            "type": "incident_help",
            "actions": [
                {"text": "🩹 Injury/Medical", "action": "navigate", "url": "/incidents/new?type=injury"},
                {"text": "🚗 Vehicle Incident", "action": "navigate", "url": "/incidents/new?type=vehicle"},
                {"text": "🌊 Environmental/Spill", "action": "navigate", "url": "/incidents/new?type=environmental"},
                {"text": "💔 Property Damage", "action": "navigate", "url": "/incidents/new?type=property"},
                {"text": "⚠️ Near Miss", "action": "navigate", "url": "/incidents/new?type=near_miss"},
                {"text": "📝 Other Incident", "action": "navigate", "url": "/incidents/new"}
            ],
            "quick_replies": [
                "Someone was injured",
                "There was property damage",
                "Chemical spill occurred",
                "It was a near miss",
                "Vehicle accident"
            ],
            "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first.",
            "debug_info": debug_info
        }
    
    elif any(word in message_lower for word in ["safety", "concern", "unsafe", "hazard"]):
        return {
            "message": "🛡️ **Thank you for speaking up about safety!**\n\nEvery safety observation helps create a safer workplace.",
            "type": "safety_help",
            "actions": [
                {"text": "⚠️ Report Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📞 Anonymous Report", "action": "navigate", "url": "/safety-concerns/new?anonymous=true"}
            ],
            "debug_info": debug_info
        }
    
    elif any(word in message_lower for word in ["sds", "chemical", "safety data sheet", "msds"]):
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and easy to navigate.",
            "type": "sds_help",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ],
            "debug_info": debug_info
        }
    
    elif any(word in message_lower for word in ["emergency", "911", "fire", "urgent"]):
        return {
            "message": "🚨 **EMERGENCY DETECTED**\n\n**FOR LIFE-THREATENING EMERGENCIES: CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568",
            "type": "emergency",
            "actions": [
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ],
            "debug_info": debug_info
        }
    
    else:
        # Default comprehensive help
        return {
            "message": "🤖 **I'm your EHS Assistant!**\n\nI can help you with:\n\n• 🚨 **Report incidents** and safety concerns\n• 📊 **Navigate the system** and find information\n• 📄 **Find safety data sheets** and documentation\n• 🔄 **Get guidance** on EHS procedures\n\nWhat would you like to work on?",
            "type": "general_help",
            "actions": [
                {"text": "🚨 Report Incident", "action": "navigate", "url": "/incidents/new"},
                {"text": "🛡️ Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"},
                {"text": "📄 Find SDS", "action": "navigate", "url": "/sds"}
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern",
                "Find SDS",
                "What's urgent?"
            ],
            "debug_info": debug_info
        }

# Debug route to help troubleshoot
@chatbot_bp.route("/chat/debug", methods=["GET"])
def chat_debug():
    """Comprehensive debug endpoint to check chatbot status"""
    chatbot = get_chatbot()
    
    debug_info = {
        "timestamp": time.time(),
        "chatbot_available": chatbot is not None,
        "chatbot_type": type(chatbot).__name__ if chatbot else None,
        "chatbot_instance_id": id(chatbot) if chatbot else None,
        "current_mode": getattr(chatbot, 'current_mode', 'unknown') if chatbot else None,
        "current_context": getattr(chatbot, 'current_context', {}) if chatbot else {},
        "slot_filling_state": getattr(chatbot, 'slot_filling_state', {}) if chatbot else {},
        "conversation_history_length": len(getattr(chatbot, 'conversation_history', [])) if chatbot else 0,
        "import_status": {
            "services_ehs_chatbot": "OK" if CHATBOT_AVAILABLE else "FAILED"
        },
        "environment": {
            "flask_env": os.environ.get("FLASK_ENV", "production"),
            "enable_sbert": os.environ.get("ENABLE_SBERT", "false"),
            "python_version": os.sys.version
        },
        "file_system": {
            "data_dir_exists": os.path.exists("data"),
            "uploads_dir_exists": os.path.exists("static/uploads"),
            "incidents_file_exists": os.path.exists("data/incidents.json")
        }
    }
    
    # Test basic functionality if chatbot available
    if chatbot:
        try:
            test_response = chatbot.process_message("test message", "debug_user")
            debug_info["test_response"] = {
                "success": True,
                "type": test_response.get("type", "unknown"),
                "has_message": bool(test_response.get("message"))
            }
        except Exception as e:
            debug_info["test_response"] = {
                "success": False,
                "error": str(e)
            }
    
    return jsonify(debug_info)

# Test route for quick incident type detection
@chatbot_bp.route("/chat/test-intent", methods=["POST"])
def test_intent():
    """Test intent detection with debugging"""
    data = request.get_json()
    message = data.get("message", "")
    
    chatbot = get_chatbot()
    if chatbot and hasattr(chatbot, 'intent_classifier'):
        try:
            intent, confidence = chatbot.intent_classifier.classify_intent(message)
            
            # Additional debugging for intent classification
            debug_info = {
                "message": message,
                "intent": intent,
                "confidence": confidence,
                "status": "success",
                "classifier_type": type(chatbot.intent_classifier).__name__,
                "patterns_matched": []
            }
            
            # Check which patterns matched
            if hasattr(chatbot.intent_classifier, 'rule_patterns'):
                for pattern_name, patterns in chatbot.intent_classifier.rule_patterns.items():
                    for pattern in patterns:
                        import re
                        if re.search(pattern, message.lower()):
                            debug_info["patterns_matched"].append({
                                "pattern_group": pattern_name,
                                "pattern": pattern
                            })
            
            return jsonify(debug_info)
            
        except Exception as e:
            return jsonify({
                "message": message,
                "error": str(e),
                "status": "error",
                "traceback": str(e) if os.getenv("FLASK_ENV") == "development" else None
            })
    else:
        return jsonify({
            "message": message,
            "error": "Chatbot or intent classifier not available",
            "status": "unavailable",
            "chatbot_available": chatbot is not None,
            "has_intent_classifier": hasattr(chatbot, 'intent_classifier') if chatbot else False
        })

@chatbot_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    """Reset chat session with debugging"""
    chatbot = get_chatbot()
    if chatbot:
        try:
            old_state = {
                "mode": getattr(chatbot, 'current_mode', 'unknown'),
                "context": dict(getattr(chatbot, 'current_context', {})),
                "slot_state": dict(getattr(chatbot, 'slot_filling_state', {}))
            }
            
            chatbot.current_mode = 'general'
            chatbot.current_context = {}
            chatbot.slot_filling_state = {}
            
            new_state = {
                "mode": getattr(chatbot, 'current_mode', 'unknown'),
                "context": dict(getattr(chatbot, 'current_context', {})),
                "slot_state": dict(getattr(chatbot, 'slot_filling_state', {}))
            }
            
            return jsonify({
                "status": "reset", 
                "message": "Chat session reset successfully",
                "old_state": old_state,
                "new_state": new_state
            })
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": f"Reset failed: {str(e)}",
                "error_details": str(e)
            })
    return jsonify({
        "status": "error", 
        "message": "Chatbot not available",
        "chatbot_available": False
    })

@chatbot_bp.route("/chat/status")
def chat_status():
    """Get comprehensive system status with detailed debugging"""
    chatbot = get_chatbot()
    
    status = {
        "timestamp": time.time(),
        "chatbot_available": chatbot is not None,
        "current_mode": getattr(chatbot, 'current_mode', 'unavailable') if chatbot else 'unavailable',
        "memory_optimized": True,
        "ml_features": False,
        "features": {
            "file_upload": True,
            "basic_intent_classification": chatbot is not None,
            "slot_filling": chatbot is not None,
            "rule_based_responses": True,
            "sbert_embeddings": False,
            "advanced_ai": False
        },
        "debug": {
            "chatbot_class": type(chatbot).__name__ if chatbot else None,
            "has_intent_classifier": hasattr(chatbot, 'intent_classifier') if chatbot else False,
            "has_slot_policy": hasattr(chatbot, 'slot_policy') if chatbot else False,
            "conversation_count": len(getattr(chatbot, 'conversation_history', [])) if chatbot else 0,
            "intent_classifier_type": type(getattr(chatbot, 'intent_classifier', None)).__name__ if chatbot and hasattr(chatbot, 'intent_classifier') else None,
            "slot_policy_type": type(getattr(chatbot, 'slot_policy', None)).__name__ if chatbot and hasattr(chatbot, 'slot_policy') else None
        },
        "system_info": {
            "python_version": os.sys.version.split()[0],
            "flask_env": os.environ.get("FLASK_ENV", "production"),
            "data_directory_exists": os.path.exists("data"),
            "uploads_directory_exists": os.path.exists("static/uploads")
        }
    }
    
    return jsonify(status)
