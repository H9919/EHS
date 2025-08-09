# routes/chatbot.py - Memory-optimized version with lazy loading
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
        except ImportError as e:
            print(f"⚠ Chatbot not available: {e}")
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
    """Memory-efficient chat interface"""
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
    try:
        # Parse request data efficiently
        user_message, user_id, context, uploaded_file = parse_request_data()
        
        # Get chatbot instance (lazy loaded)
        chatbot = get_chatbot()
        
        if chatbot:
            response = chatbot.process_message(user_message, user_id, context)
            
            # Add minimal system context
            response["system_context"] = {
                "mode": getattr(chatbot, 'current_mode', 'general'),
                "memory_optimized": True
            }
            
            return jsonify(response)
        else:
            # Lightweight fallback without heavy imports
            return jsonify(get_lightweight_fallback_response(user_message, uploaded_file))
            
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "message": "I'm having trouble processing your request. Let me direct you to the right place.",
            "type": "error",
            "actions": [
                {
                    "text": "📝 Report Incident",
                    "action": "navigate",
                    "url": "/incidents/new"
                },
                {
                    "text": "📊 Dashboard",
                    "action": "navigate", 
                    "url": "/dashboard"
                }
            ]
        })

def parse_request_data():
    """Efficiently parse request data"""
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

def handle_file_upload_efficient(file):
    """Handle file upload with minimal memory usage"""
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
    
    # Simple keyword-based responses (no ML needed)
    if any(word in message_lower for word in ["incident", "accident", "injury", "hurt", "damage"]):
        return {
            "message": "🚨 **I'll help you report this incident.**\n\nLet me guide you to our incident reporting system.",
            "type": "incident_help",
            "actions": [
                {"text": "🩹 Injury Incident", "action": "navigate", "url": "/incidents/new?type=injury"},
                {"text": "🚗 Vehicle Incident", "action": "navigate", "url": "/incidents/new?type=vehicle"},
                {"text": "🌊 Environmental Spill", "action": "navigate", "url": "/incidents/new?type=environmental"},
                {"text": "📝 General Incident", "action": "navigate", "url": "/incidents/new"}
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
    
    elif any(word in message_lower for word in ["sds", "chemical", "safety data sheet"]):
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and easy to navigate.",
            "type": "sds_help",
            "actions": [
                {"text": "🔍 Search SDS Library", "action": "navigate", "url": "/sds"},
                {"text": "📤 Upload New SDS", "action": "navigate", "url": "/sds/upload"}
            ]
        }
    
    elif any(word in message_lower for word in ["dashboard", "overview", "status", "urgent"]):
        return {
            "message": "📊 **EHS System Overview**\n\nI can help you navigate to different areas of the system.",
            "type": "dashboard_help",
            "actions": [
                {"text": "📊 View Dashboard", "action": "navigate", "url": "/dashboard"},
                {"text": "📋 View Incidents", "action": "navigate", "url": "/incidents"},
                {"text": "🔄 View CAPAs", "action": "navigate", "url": "/capa"}
            ]
        }
    
    elif any(word in message_lower for word in ["emergency", "911", "fire", "urgent help"]):
        return {
            "message": "🚨 **EMERGENCY DETECTED**\n\n**FOR LIFE-THREATENING EMERGENCIES: CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568",
            "type": "emergency",
            "actions": [
                {"text": "📝 Report Emergency Incident", "action": "navigate", "url": "/incidents/new?type=emergency"}
            ]
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

@chatbot_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    """Reset chat session"""
    chatbot = get_chatbot()
    if chatbot:
        chatbot.current_mode = 'general'
        chatbot.current_context = {}
        chatbot.slot_filling_state = {}
        return jsonify({"status": "reset", "message": "Chat session reset successfully"})
    return jsonify({"status": "error", "message": "Chatbot not available"})

@chatbot_bp.route("/chat/history")
def chat_history():
    """Get chat history (lightweight)"""
    chatbot = get_chatbot()
    if chatbot:
        # Return only essential data to save memory
        history = getattr(chatbot, 'conversation_history', [])
        return jsonify({
            "history": history[-10:],  # Only last 10 messages
            "current_mode": getattr(chatbot, 'current_mode', 'general'),
            "count": len(history)
        })
    return jsonify({"history": [], "current_mode": "general", "count": 0})

@chatbot_bp.route("/chat/summary")
def chat_summary():
    """Get lightweight conversation summary"""
    chatbot = get_chatbot()
    if chatbot:
        return jsonify(chatbot.get_conversation_summary())
    return jsonify({"summary": "Chatbot service not available", "message_count": 0})

@chatbot_bp.route("/chat/status")
def chat_status():
    """Get system status without heavy operations"""
    chatbot = get_chatbot()
    
    status = {
        "chatbot_available": chatbot is not None,
        "current_mode": getattr(chatbot, 'current_mode', 'unavailable') if chatbot else 'unavailable',
        "memory_optimized": True,
        "ml_features": False,  # Disabled for memory savings
        "features": {
            "file_upload": True,
            "basic_intent_classification": True,
            "slot_filling": True,
            "rule_based_responses": True,
            "sbert_embeddings": False,  # Disabled
            "advanced_ai": False  # Disabled
        }
    }
    
    return jsonify(status)

# Lightweight incident enhancement (without heavy AI processing)
@chatbot_bp.route("/incidents/<incident_id>/quick-assess", methods=["POST"])
def quick_incident_assessment(incident_id):
    """Quick incident assessment without heavy AI"""
    try:
        # Load incident data
        incidents_file = Path("data/incidents.json")
        if not incidents_file.exists():
            return jsonify({"error": "No incidents found"}), 404
        
        incidents = json.loads(incidents_file.read_text())
        incident = incidents.get(incident_id)
        
        if not incident:
            return jsonify({"error": "Incident not found"}), 404
        
        # Simple rule-based assessment
        assessment = simple_risk_assessment(incident)
        
        # Update incident
        incident["quick_assessment"] = assessment
        incident["assessed_at"] = time.time()
        
        incidents[incident_id] = incident
        incidents_file.write_text(json.dumps(incidents, indent=2))
        
        return jsonify({
            "status": "assessed",
            "assessment": assessment,
            "message": "Quick assessment completed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def simple_risk_assessment(incident_data):
    """Simple rule-based risk assessment"""
    answers = incident_data.get("answers", {})
    incident_type = incident_data.get("type", "other")
    
    # Combine all text for analysis
    all_text = " ".join([
        answers.get("people", ""),
        answers.get("environment", ""),
        answers.get("cost", ""),
        answers.get("legal", ""),
        answers.get("reputation", "")
    ]).lower()
    
    # High risk indicators
    high_risk_words = [
        "severe", "serious", "hospital", "major", "significant", 
        "fatality", "death", "unconscious", "surgery", "amputation"
    ]
    
    # Medium risk indicators
    medium_risk_words = [
        "medical", "treatment", "injury", "spill", "damage",
        "lost time", "restricted", "reportable"
    ]
    
    # Low risk indicators
    low_risk_words = [
        "minor", "first aid", "superficial", "small", "negligible",
        "near miss", "no injury"
    ]
    
    # Calculate risk level
    high_score = sum(1 for word in high_risk_words if word in all_text)
    medium_score = sum(1 for word in medium_risk_words if word in all_text) 
    low_score = sum(1 for word in low_risk_words if word in all_text)
    
    if high_score > 0:
        risk_level = "High"
        severity = 8
        likelihood = 6
    elif medium_score > low_score:
        risk_level = "Medium"
        severity = 5
        likelihood = 5
    else:
        risk_level = "Low"
        severity = 2
        likelihood = 3
    
    # Adjust based on incident type
    type_adjustments = {
        "injury": {"severity": 1, "likelihood": 0},
        "environmental": {"severity": 1, "likelihood": -1},
        "near_miss": {"severity": -2, "likelihood": 1}
    }
    
    if incident_type in type_adjustments:
        adj = type_adjustments[incident_type]
        severity = max(1, min(10, severity + adj["severity"]))
        likelihood = max(1, min(10, likelihood + adj["likelihood"]))
    
    risk_score = severity * likelihood
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "severity": severity,
        "likelihood": likelihood,
        "rationale": f"Based on keyword analysis of {incident_type} incident",
        "method": "rule_based"
    }

# Memory-efficient SDS search
@chatbot_bp.route("/sds/simple-search", methods=["POST"])
def simple_sds_search():
    """Simple SDS search without heavy embeddings"""
    try:
        data = request.get_json()
        query = data.get("query", "").lower()
        
        # Load SDS index
        sds_file = Path("data/sds/index.json")
        if not sds_file.exists():
            return jsonify({"results": [], "message": "No SDS found"})
        
        sds_index = json.loads(sds_file.read_text())
        
        # Simple keyword matching
        results = []
        for sds_id, sds_data in sds_index.items():
            product_name = sds_data.get("product_name", "").lower()
            file_name = sds_data.get("file_name", "").lower()
            
            # Check for keyword matches
            if (query in product_name or 
                query in file_name or
                any(query in chunk.lower() for chunk in sds_data.get("chunks", [])[:3])):  # Only check first 3 chunks
                
                results.append({
                    "sds_id": sds_id,
                    "product_name": sds_data.get("product_name"),
                    "file_name": sds_data.get("file_name"),
                    "relevance": "keyword_match"
                })
        
        # Limit results to save memory
        results = results[:10]
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
            "method": "keyword_search"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@chatbot_bp.route("/health")
def health_check():
    """Lightweight health check"""
    return jsonify({
        "status": "healthy",
        "memory_optimized": True,
        "chatbot_available": get_chatbot() is not None,
        "timestamp": time.time()
    })
