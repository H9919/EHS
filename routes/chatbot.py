# routes/chatbot.py - WORKING chatbot route (simplified)
import json
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template

chatbot_bp = Blueprint("chatbot", __name__)

# Import the working chatbot
try:
    from services.ehs_chatbot import EHSChatbot
    chatbot = EHSChatbot()
    CHATBOT_AVAILABLE = True
except ImportError as e:
    print(f"EHS Chatbot not available: {e}")
    CHATBOT_AVAILABLE = False
    chatbot = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = Path("static/uploads")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    # Handle POST requests (actual chat)
    try:
        # Handle both JSON and form data (for file uploads)
        if request.is_json:
            data = request.get_json()
            user_message = data.get("message", "")
            user_id = data.get("user_id", "default_user")
            context = data.get("context", {})
            uploaded_file = None
        else:
            user_message = request.form.get("message", "")
            user_id = request.form.get("user_id", "default_user")
            context_str = request.form.get("context", "{}")
            try:
                context = json.loads(context_str)
            except:
                context = {}
            
            # Handle file upload
            uploaded_file = None
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    ensure_upload_dir()
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid conflicts
                    import time
                    timestamp = str(int(time.time()))
                    name, ext = os.path.splitext(filename)
                    unique_filename = f"{name}_{timestamp}{ext}"
                    file_path = UPLOAD_FOLDER / unique_filename
                    file.save(file_path)
                    
                    uploaded_file = {
                        "filename": filename,
                        "path": str(file_path),
                        "type": file.content_type,
                        "size": os.path.getsize(file_path)
                    }
        
        # Update context with file info if present
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            # If no message but file uploaded, create a contextual message
            if not user_message.strip():
                file_type = uploaded_file["type"]
                if file_type.startswith('image/'):
                    user_message = f"I've uploaded an image ({uploaded_file['filename']}) for my report or incident"
                elif file_type == 'application/pdf':
                    user_message = f"I've uploaded a PDF document ({uploaded_file['filename']})"
                else:
                    user_message = f"I've uploaded a file ({uploaded_file['filename']})"
        
        # If chatbot is available, use it
        if CHATBOT_AVAILABLE and chatbot:
            response = chatbot.process_message(user_message, user_id, context)
            return jsonify(response)
        else:
            # Fallback response if chatbot service isn't available
            return jsonify(get_fallback_response(user_message, uploaded_file))
            
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "message": "I apologize, but I encountered an error processing your request. Let me help you navigate to the right place instead.",
            "type": "error",
            "actions": [
                {
                    "text": "📝 Report Incident",
                    "action": "navigate",
                    "url": "/incidents/new"
                },
                {
                    "text": "🛡️ Safety Concern", 
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📊 Dashboard",
                    "action": "navigate", 
                    "url": "/dashboard"
                }
            ]
        })

def get_fallback_response(message: str, uploaded_file: Dict = None) -> Dict:
    """Fallback responses when main chatbot isn't available"""
    message_lower = message.lower()
    
    # Handle file uploads
    if uploaded_file:
        filename = uploaded_file.get("filename", "")
        file_type = uploaded_file.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this image for reporting. Where would you like to go?",
                "type": "file_upload",
                "actions": [
                    {
                        "text": "🚨 Report Incident",
                        "action": "navigate",
                        "url": "/incidents/new"
                    },
                    {
                        "text": "🛡️ Safety Concern",
                        "action": "navigate",
                        "url": "/safety-concerns/new"
                    }
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis looks like it could be a Safety Data Sheet or document. Where should I direct you?",
                "type": "file_upload",
                "actions": [
                    {
                        "text": "📋 Upload to SDS Library",
                        "action": "navigate",
                        "url": "/sds/upload"
                    },
                    {
                        "text": "📎 Use for Documentation",
                        "action": "navigate",
                        "url": "/incidents/new"
                    }
                ]
            }
    
    # Handle specific intents
    if any(word in message_lower for word in ["incident", "accident", "injury", "report incident", "workplace incident"]):
        return {
            "message": "🚨 **I'll help you report a workplace incident.**\n\nLet me direct you to our incident reporting system where you can provide all the necessary details.",
            "type": "incident_help",
            "actions": [
                {
                    "text": "🩹 Injury Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=injury"
                },
                {
                    "text": "🚗 Vehicle Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=vehicle"
                },
                {
                    "text": "🌊 Environmental Spill",
                    "action": "navigate",
                    "url": "/incidents/new?type=environmental"
                },
                {
                    "text": "💔 Property Damage",
                    "action": "navigate",
                    "url": "/incidents/new?type=property"
                },
                {
                    "text": "📝 General Incident Form",
                    "action": "navigate",
                    "url": "/incidents/new"
                }
            ],
            "quick_replies": [
                "Someone was injured",
                "There was property damage",
                "Environmental incident occurred",
                "It was a near miss"
            ]
        }
    
    elif any(word in message_lower for word in ["safety concern", "unsafe", "hazard", "dangerous", "concern"]):
        return {
            "message": "🛡️ **Thank you for speaking up about a safety concern!**\n\nEvery safety observation helps prevent incidents. Let me direct you to our safety reporting system.",
            "type": "safety_help",
            "actions": [
                {
                    "text": "⚠️ Report Safety Concern",
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📞 Anonymous Report",
                    "action": "navigate",
                    "url": "/safety-concerns/new?anonymous=true"
                },
                {
                    "text": "📋 View All Concerns",
                    "action": "navigate",
                    "url": "/safety-concerns"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["risk", "assessment", "evaluate", "risk assessment"]):
        return {
            "message": "📊 **I'll help you with risk assessment.**\n\nOur system uses the ERC (Event Risk Classification) matrix to evaluate likelihood and severity.",
            "type": "risk_help",
            "actions": [
                {
                    "text": "🎯 Start Risk Assessment",
                    "action": "navigate",
                    "url": "/risk/assess"
                },
                {
                    "text": "📋 View Risk Register",
                    "action": "navigate",
                    "url": "/risk/register"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["capa", "corrective", "preventive", "action"]):
        return {
            "message": "🔄 **I'll help you with Corrective and Preventive Actions (CAPA).**\n\nCAPAs help us learn from incidents and improve our safety performance.",
            "type": "capa_help",
            "actions": [
                {
                    "text": "➕ Create New CAPA",
                    "action": "navigate",
                    "url": "/capa/new"
                },
                {
                    "text": "📊 CAPA Dashboard",
                    "action": "navigate",
                    "url": "/capa/dashboard"
                },
                {
                    "text": "📋 View All CAPAs",
                    "action": "navigate",
                    "url": "/capa"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["sds", "safety data sheet", "chemical", "material"]):
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and includes AI chat functionality for asking questions about chemicals.",
            "type": "sds_help",
            "actions": [
                {
                    "text": "🔍 Search SDS Library",
                    "action": "navigate",
                    "url": "/sds"
                },
                {
                    "text": "📤 Upload New SDS",
                    "action": "navigate",
                    "url": "/sds/upload"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["dashboard", "overview", "status", "urgent", "attention", "summary"]):
        return {
            "message": "📊 **Here's your EHS system overview.**\n\nLet me direct you to the areas that need your attention.",
            "type": "dashboard_help",
            "actions": [
                {
                    "text": "📊 Full Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                },
                {
                    "text": "📋 View Incidents",
                    "action": "navigate",
                    "url": "/incidents"
                },
                {
                    "text": "🔄 View CAPAs",
                    "action": "navigate",
                    "url": "/capa"
                },
                {
                    "text": "🛡️ Safety Concerns",
                    "action": "navigate",
                    "url": "/safety-concerns"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["emergency", "911", "fire", "urgent help"]):
        return {
            "message": "🚨 **EMERGENCY DETECTED**\n\n**FOR LIFE-THREATENING EMERGENCIES: CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569",
            "type": "emergency",
            "actions": [
                {
                    "text": "📝 Report Emergency Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency"
                }
            ]
        }
    
    elif any(word in message_lower for word in ["help", "guide", "how", "what can you do"]):
        return {
            "message": "🤖 **I'm your Smart EHS Assistant!**\n\nI can help you navigate to the right place for:\n\n• 🚨 **Incident reporting** - Workplace accidents and injuries\n• 🛡️ **Safety concerns** - Unsafe conditions or behaviors\n• 📊 **Risk assessments** - Evaluate workplace risks\n• 🔄 **CAPAs** - Corrective and preventive actions\n• 📄 **SDS lookup** - Safety data sheets for chemicals\n• 📊 **Dashboard** - System overview and urgent items\n\nWhat would you like to work on?",
            "type": "help_menu",
            "actions": [
                {
                    "text": "🚨 Report Incident",
                    "action": "navigate",
                    "url": "/incidents/new"
                },
                {
                    "text": "🛡️ Safety Concern",
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📊 View Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ]
        }
    
    else:
        # Default response
        return {
            "message": "🤖 **I'm here to help with your EHS needs!**\n\nI can direct you to the right place for:\n\n• **Reporting incidents** and safety concerns\n• **Risk assessments** and safety analysis\n• **Finding information** like safety data sheets\n• **Managing CAPAs** and corrective actions\n• **System overviews** and urgent items\n\nWhat would you like to work on?",
            "type": "general_help",
            "actions": [
                {
                    "text": "🚨 Report Incident",
                    "action": "navigate",
                    "url": "/incidents/new"
                },
                {
                    "text": "🛡️ Safety Concern",
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📊 Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                },
                {
                    "text": "📄 Find SDS",
                    "action": "navigate",
                    "url": "/sds"
                }
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern",
                "Risk assessment",
                "Find SDS",
                "What's urgent?"
            ]
        }

@chatbot_bp.route("/chat/history")
def chat_history():
    if CHATBOT_AVAILABLE and chatbot:
        return jsonify(chatbot.conversation_history[-20:])
    else:
        return jsonify([])

@chatbot_bp.route("/chat/summary")
def chat_summary():
    if CHATBOT_AVAILABLE and chatbot:
        return jsonify(chatbot.get_conversation_summary())
    else:
        return jsonify({"summary": "Chatbot service not available"})
