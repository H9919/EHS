# routes/chatbot.py - Fixed version with better error handling and debugging
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
    """Memory-efficient chat interface with better error handling"""
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    try:
        # Parse request data efficiently
        user_message, user_id, context, uploaded_file = parse_request_data()
        
        print(f"DEBUG: Received message: '{user_message}', context: {context}")
        
        # Get chatbot instance (lazy loaded)
        chatbot = get_chatbot()
        
        if chatbot:
            try:
                response = chatbot.process_message(user_message, user_id, context)
                
                # Add minimal system context
                response["system_context"] = {
                    "mode": getattr(chatbot, 'current_mode', 'general'),
                    "memory_optimized": True,
                    "debug_info": {
                        "message_processed": True,
                        "context_keys": list(context.keys()) if context else [],
                        "current_context": getattr(chatbot, 'current_context', {}),
                        "slot_state": getattr(chatbot, 'slot_filling_state', {})
                    }
                }
                
                print(f"DEBUG: Response generated: {response.get('type', 'unknown')}")
                return jsonify(response)
                
            except Exception as e:
                print(f"ERROR: Chatbot processing failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Return enhanced fallback with debugging info
                return jsonify(get_enhanced_fallback_with_debug(user_message, uploaded_file, str(e)))
        else:
            print("WARNING: Chatbot not available, using fallback")
            # Lightweight fallback without heavy imports
            return jsonify(get_lightweight_fallback_response(user_message, uploaded_file))
            
    except Exception as e:
        print(f"ERROR: Chat route exception: {e}")
        import traceback
        traceback.print_exc()
        
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
            "debug_error": str(e) if os.getenv("FLASK_ENV") == "development" else None
        })

def parse_request_data():
    """Efficiently parse request data"""
    try:
        if request.is_json:
            data = request.get_json()
            user_message = data.get("message", "")
            user_id = data.get("user_id", "default_user")
            context = data.get("context", {})
            uploaded_file = None
        else:
            user_message = request.form.get("message", "")
            user_id = request.form.get("user_id", "default_user")
            context = {}
            
            # Handle file upload
            uploaded_file = None
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    uploaded_file = handle_file_upload_efficient(file)
        
        # Update context with file info if present
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            if not user_message.strip():
                user_message = f"I've uploaded a file ({uploaded_file['filename']})"
        
        return user_message, user_id, context, uploaded_file
        
    except Exception as e:
        print(f"ERROR: Failed to parse request data: {e}")
        return "", "default_user", {}, None

def handle_file_upload_efficient(file):
    """Handle file upload with minimal memory usage"""
    try:
        ensure_upload_dir()
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        file_path = UPLOAD_FOLDER / unique_filename
        
        # Save file
        file.save(file_path)
        
        return {
            "filename": filename,
            "path": str(file_path),
            "type": file.content_type or "application/octet-stream",
            "size": os.path.getsize(file_path)
        }
    except Exception as e:
        print(f"ERROR: File upload failed: {e}")
        return None

def get_enhanced_fallback_with_debug(message, uploaded_file=None, error_msg=""):
    """Enhanced fallback with debugging information"""
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
                "error": error_msg
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
            ]
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
            ]
        }
    
    elif any(word in message_lower for word in ["damage", "property", "broken", "equipment"]):
        return {
            "message": "💔 **I understand this involves property damage.**\n\nLet me direct you to our property damage incident reporting form.",
            "type": "property_incident_direct",
            "actions": [
                {
                    "text": "💔 Report Property Damage",
                    "action": "navigate",
                    "url": "/incidents/new?type=property"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["near miss", "almost", "could have"]):
        return {
            "message": "⚠️ **I understand this was a near miss incident.**\n\nThank you for reporting this - near misses help us prevent actual incidents.",
            "type": "near_miss_direct",
            "actions": [
                {
                    "text": "⚠️ Report Near Miss",
                    "action": "navigate",
                    "url": "/incidents/new?type=near_miss"
                }
            ]
        }
    
    # Default enhanced fallback
    return get_lightweight_fallback_response(message, uploaded_file)

def get_lightweight_fallback_response(message, uploaded_file=None):
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
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis could be a Safety Data Sheet or documentation.",
                "type": "file_upload",
                "actions": [
                    {"text": "📋 Add to SDS Library", "action": "navigate", "url": "/sds/upload"}
                ]
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
            "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first."
        }
    
    elif any(word in message_lower for word in ["safety", "concern", "unsafe", "hazard"]):
        return {
            "message": "🛡️ **Thank you for speaking up about safety!**\n\nEvery safety observation helps create a safer workplace.",
            "type": "safety_help",
            "actions": [
                {"text": "⚠️ Report Safety Concern", "action": "navigate", "url": "/safety-concerns/new"},
                {"text": "📞 Anonymous Report", "action": "navigate", "url": "/safety-concerns/new?anonymous=true"}
            ]
        }
    
    elif any(word in message_lower for word in ["sds", "chemical", "safety data sheet", "msds"]):
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and easy to navigate.",
            "type": "sds_help",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ]
        }
    
    elif any(word in message_lower for word in ["emergency", "911", "fire", "urgent"]):
        return {
            "message": "🚨 **EMERGENCY DETECTED**\n\n**FOR LIFE-THREATENING EMERGENCIES: CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568",
            "type": "emergency",
            "actions": [
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ]
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
            ]
        }

# Debug route to help troubleshoot
@chatbot_bp.route("/chat/debug", methods=["GET"])
def chat_debug():
    """Debug endpoint to check chatbot status"""
    chatbot = get_chatbot()
    
    debug_info = {
        "chatbot_available": chatbot is not None,
        "chatbot_type": type(chatbot).__name__ if chatbot else None,
        "current_mode": getattr(chatbot, 'current_mode', 'unknown') if chatbot else None,
        "current_context": getattr(chatbot, 'current_context', {}) if chatbot else {},
        "slot_filling_state": getattr(chatbot, 'slot_filling_state', {}) if chatbot else {},
        "conversation_history_length": len(getattr(chatbot, 'conversation_history', [])) if chatbot else 0,
        "import_status": {
            "services_ehs_chatbot": "OK" if CHATBOT_AVAILABLE else "FAILED"
        }
    }
    
    return jsonify(debug_info)

# Test route for quick incident type detection
@chatbot_bp.route("/chat/test-intent", methods=["POST"])
def test_intent():
    """Test intent detection"""
    data = request.get_json()
    message = data.get("message", "")
    
    chatbot = get_chatbot()
    if chatbot and hasattr(chatbot, 'intent_classifier'):
        try:
            intent, confidence = chatbot.intent_classifier.classify_intent(message)
            return jsonify({
                "message": message,
                "intent": intent,
                "confidence": confidence,
                "status": "success"
            })
        except Exception as e:
            return jsonify({
                "message": message,
                "error": str(e),
                "status": "error"
            })
    else:
        return jsonify({
            "message": message,
            "error": "Chatbot or intent classifier not available",
            "status": "unavailable"
        })

@chatbot_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    """Reset chat session"""
    chatbot = get_chatbot()
    if chatbot:
        try:
            chatbot.current_mode = 'general'
            chatbot.current_context = {}
            chatbot.slot_filling_state = {}
            return jsonify({"status": "reset", "message": "Chat session reset successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Reset failed: {str(e)}"})
    return jsonify({"status": "error", "message": "Chatbot not available"})

@chatbot_bp.route("/chat/status")
def chat_status():
    """Get system status with detailed debugging"""
    chatbot = get_chatbot()
    
    status = {
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
            "conversation_count": len(getattr(chatbot, 'conversation_history', [])) if chatbot else 0
        }
    }
    
    return jsonify(status)
