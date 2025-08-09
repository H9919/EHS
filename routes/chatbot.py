# routes/chatbot.py - FIXED VERSION with proper error handling
import json
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template

chatbot_bp = Blueprint("chatbot", __name__)

# Global chatbot instance - lazy loaded
_chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance with proper error handling"""
    global _chatbot_instance
    
    if _chatbot_instance is None:
        try:
            from services.ehs_chatbot import create_chatbot
            _chatbot_instance = create_chatbot()
            if _chatbot_instance:
                print("✓ Chatbot loaded successfully")
            else:
                print("⚠ Chatbot creation returned None")
        except Exception as e:
            print(f"⚠ Chatbot loading error: {e}")
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
    """Fixed chat interface with comprehensive error handling"""
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    try:
        # Parse request data with validation
        user_message, user_id, context, uploaded_file = parse_request_data_safe()
        
        print(f"DEBUG: Chat request - message: '{user_message[:100]}...', has_file: {bool(uploaded_file)}")
        
        # Get chatbot instance
        chatbot = get_chatbot()
        
        if not chatbot:
            return jsonify(get_fallback_response(user_message, uploaded_file))
        
        try:
            # Process with chatbot
            response = chatbot.process_message(user_message, user_id, context)
            
            # Validate response format
            if not isinstance(response, dict):
                print(f"ERROR: Invalid response type: {type(response)}")
                return jsonify(get_fallback_response(user_message, uploaded_file))
            
            # Ensure required fields
            if "message" not in response:
                response["message"] = "I processed your request, but couldn't generate a proper response."
            
            if "type" not in response:
                response["type"] = "general_response"
            
            print(f"DEBUG: Response generated successfully: {response.get('type')}")
            return jsonify(response)
            
        except Exception as e:
            print(f"ERROR: Chatbot processing failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify(get_fallback_response(user_message, uploaded_file, str(e)))
    
    except Exception as e:
        print(f"ERROR: Chat route exception: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "message": "I'm having trouble processing your request. Please try the navigation menu or contact support.",
            "type": "error",
            "actions": [
                {"text": "📝 Report Incident", "action": "navigate", "url": "/incidents/new"},
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        })

def parse_request_data_safe():
    """Safely parse request data with comprehensive validation"""
    try:
        user_message = ""
        user_id = "default_user"
        context = {}
        uploaded_file = None
        
        if request.is_json:
            # JSON request
            data = request.get_json() or {}
            user_message = str(data.get("message", "")).strip()
            user_id = str(data.get("user_id", "default_user"))
            context = data.get("context", {})
            
            if not isinstance(context, dict):
                context = {}
                
        else:
            # Form request
            user_message = str(request.form.get("message", "")).strip()
            user_id = str(request.form.get("user_id", "default_user"))
            
            # Handle file upload
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    uploaded_file = handle_file_upload_safe(file)
        
        # Add file info to context
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            if not user_message:
                user_message = f"I've uploaded a file: {uploaded_file.get('filename', 'unknown')}"
        
        # Validate message length
        if len(user_message) > 5000:
            user_message = user_message[:5000] + "..."
        
        return user_message, user_id, context, uploaded_file
        
    except Exception as e:
        print(f"ERROR: Failed to parse request data: {e}")
        return "", "default_user", {}, None

def handle_file_upload_safe(file):
    """Safely handle file upload with error handling"""
    try:
        ensure_upload_dir()
        
        filename = secure_filename(file.filename)
        if not filename:
            return None
        
        # Add timestamp to avoid conflicts
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        file_path = UPLOAD_FOLDER / unique_filename
        
        # Save file
        file.save(file_path)
        
        file_info = {
            "filename": filename,
            "path": str(file_path),
            "type": file.content_type or "application/octet-stream",
            "size": os.path.getsize(file_path)
        }
        
        print(f"DEBUG: File uploaded successfully: {file_info}")
        return file_info
        
    except Exception as e:
        print(f"ERROR: File upload failed: {e}")
        return None

def get_fallback_response(message, uploaded_file=None, error_msg=""):
    """Generate intelligent fallback response"""
    try:
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
        
        # Smart keyword-based responses
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
                    "Property damage occurred",
                    "Chemical spill happened",
                    "It was a near miss",
                    "Vehicle accident"
                ]
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
                "type": "emergency"
            }
        
        else:
            # Default help response
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
    
    except Exception as e:
        print(f"ERROR: Fallback response generation failed: {e}")
        return {
            "message": "I'm here to help with EHS matters. Use the navigation menu to access specific features.",
            "type": "basic_fallback",
            "actions": [
                {"text": "📊 Dashboard", "action": "navigate", "url": "/dashboard"}
            ]
        }

@chatbot_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    """Reset chat session"""
    try:
        chatbot = get_chatbot()
        if chatbot:
            chatbot._reset_state()
            return jsonify({
                "status": "reset",
                "message": "Chat session reset successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Chatbot not available"
            })
    except Exception as e:
        print(f"ERROR: Chat reset failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Reset failed"
        })

@chatbot_bp.route("/chat/status")
def chat_status():
    """Get chat system status"""
    try:
        chatbot = get_chatbot()
        
        return jsonify({
            "timestamp": time.time(),
            "chatbot_available": chatbot is not None,
            "current_mode": getattr(chatbot, 'current_mode', 'unavailable') if chatbot else 'unavailable',
            "features": {
                "file_upload": True,
                "incident_reporting": True,
                "safety_concerns": True,
                "sds_lookup": True,
                "emergency_detection": True
            },
            "system_info": {
                "python_version": os.sys.version.split()[0],
                "data_directory_exists": os.path.exists("data"),
                "uploads_directory_exists": os.path.exists("static/uploads")
            }
        })
    except Exception as e:
        print(f"ERROR: Status check failed: {e}")
        return jsonify({
            "timestamp": time.time(),
            "chatbot_available": False,
            "error": str(e)
        }), 500

@chatbot_bp.route("/chat/debug", methods=["GET"])
def chat_debug():
    """Debug endpoint for troubleshooting"""
    try:
        chatbot = get_chatbot()
        
        debug_info = {
            "timestamp": time.time(),
            "chatbot_available": chatbot is not None,
            "chatbot_type": type(chatbot).__name__ if chatbot else None,
            "current_mode": getattr(chatbot, 'current_mode', 'unknown') if chatbot else None,
            "current_context": getattr(chatbot, 'current_context', {}) if chatbot else {},
            "slot_filling_state": getattr(chatbot, 'slot_filling_state', {}) if chatbot else {},
            "environment": {
                "flask_env": os.environ.get("FLASK_ENV", "production"),
                "python_version": os.sys.version
            },
            "file_system": {
                "data_dir_exists": os.path.exists("data"),
                "uploads_dir_exists": os.path.exists("static/uploads"),
                "incidents_file_exists": os.path.exists("data/incidents.json")
            }
        }
        
        # Test basic functionality
        if chatbot:
            try:
                test_response = chatbot.process_message("test")
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
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": time.time()
        }), 500
