# routes/chatbot.py - Enhanced with proper file upload and form integration
import json
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for

chatbot_bp = Blueprint("chatbot", __name__)

# Import the enhanced chatbot
try:
    from services.ehs_chatbot import EHSChatbot
    chatbot = EHSChatbot()
    CHATBOT_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced EHS Chatbot not available: {e}")
    CHATBOT_AVAILABLE = False
    chatbot = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = Path("static/uploads")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_dir():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    """Enhanced chat interface with file upload support"""
    if request.method == "GET":
        return render_template("enhanced_dashboard.html")
    
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
                    timestamp = str(int(time.time()))
                    name, ext = os.path.splitext(filename)
                    unique_filename = f"{name}_{timestamp}{ext}"
                    file_path = UPLOAD_FOLDER / unique_filename
                    file.save(file_path)
                    
                    uploaded_file = {
                        "filename": filename,
                        "path": str(file_path),
                        "type": file.content_type or "application/octet-stream",
                        "size": os.path.getsize(file_path)
                    }
        
        # Update context with file info if present
        if uploaded_file:
            context["uploaded_file"] = uploaded_file
            # If no message but file uploaded, create a contextual message
            if not user_message.strip():
                file_type = uploaded_file["type"]
                if file_type.startswith('image/'):
                    user_message = f"I've uploaded an image ({uploaded_file['filename']}) for my report"
                elif file_type == 'application/pdf':
                    user_message = f"I've uploaded a PDF document ({uploaded_file['filename']})"
                else:
                    user_message = f"I've uploaded a file ({uploaded_file['filename']})"
        
        # Process with enhanced chatbot if available
        if CHATBOT_AVAILABLE and chatbot:
            response = chatbot.process_message(user_message, user_id, context)
            
            # Add system context
            response["system_context"] = {
                "mode": chatbot.current_mode,
                "slot_filling_active": bool(chatbot.slot_filling_state),
                "conversation_length": len(chatbot.conversation_history)
            }
            
            return jsonify(response)
        else:
            # Enhanced fallback response
            return jsonify(get_enhanced_fallback_response(user_message, uploaded_file, context))
            
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
            ],
            "error_details": str(e) if os.getenv("FLASK_ENV") == "development" else None
        })

@chatbot_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    """Reset chat session"""
    if CHATBOT_AVAILABLE and chatbot:
        chatbot.current_mode = 'general'
        chatbot.current_context = {}
        chatbot.slot_filling_state = {}
        return jsonify({"status": "reset", "message": "Chat session reset successfully"})
    return jsonify({"status": "error", "message": "Chatbot not available"})

@chatbot_bp.route("/chat/history")
def chat_history():
    """Get chat history"""
    if CHATBOT_AVAILABLE and chatbot:
        return jsonify({
            "history": chatbot.conversation_history[-20:],
            "current_mode": chatbot.current_mode,
            "active_context": bool(chatbot.current_context)
        })
    else:
        return jsonify({"history": [], "current_mode": "general", "active_context": False})

@chatbot_bp.route("/chat/summary")
def chat_summary():
    """Get conversation summary with analytics"""
    if CHATBOT_AVAILABLE and chatbot:
        return jsonify(chatbot.get_conversation_summary())
    else:
        return jsonify({"summary": "Chatbot service not available", "message_count": 0})

@chatbot_bp.route("/chat/export", methods=["POST"])
def export_chat():
    """Export chat conversation to various formats"""
    if not CHATBOT_AVAILABLE or not chatbot:
        return jsonify({"error": "Chatbot not available"}), 500
    
    export_format = request.json.get("format", "json")
    
    if export_format == "json":
        return jsonify({
            "conversation_history": chatbot.conversation_history,
            "summary": chatbot.get_conversation_summary(),
            "exported_at": time.time()
        })
    elif export_format == "text":
        # Generate text summary
        text_summary = generate_text_summary(chatbot.conversation_history)
        return jsonify({"text_summary": text_summary})
    else:
        return jsonify({"error": "Unsupported export format"}), 400

def generate_text_summary(conversation_history):
    """Generate human-readable text summary of conversation"""
    if not conversation_history:
        return "No conversation history available."
    
    summary = "EHS Chat Conversation Summary\n"
    summary += "=" * 40 + "\n\n"
    
    for i, exchange in enumerate(conversation_history, 1):
        summary += f"Exchange {i} (Intent: {exchange.get('intent', 'unknown')})\n"
        summary += f"User: {exchange.get('user', '')}\n"
        summary += f"Assistant: {exchange.get('bot', '')[:200]}...\n"
        summary += f"Time: {exchange.get('timestamp', '')}\n\n"
    
    return summary

def get_enhanced_fallback_response(message, uploaded_file=None, context=None):
    """Enhanced fallback responses with better intent detection"""
    message_lower = message.lower() if message else ""
    context = context or {}
    
    # Handle file uploads
    if uploaded_file:
        filename = uploaded_file.get("filename", "")
        file_type = uploaded_file.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this image for reporting. This could be valuable evidence for incident documentation or safety observations.",
                "type": "file_upload",
                "actions": [
                    {
                        "text": "🚨 Report Incident with Photo",
                        "action": "navigate",
                        "url": "/incidents/new"
                    },
                    {
                        "text": "🛡️ Safety Concern with Photo",
                        "action": "navigate",
                        "url": "/safety-concerns/new"
                    },
                    {
                        "text": "📋 Use for Audit Documentation",
                        "action": "navigate",
                        "url": "/audits/new"
                    }
                ],
                "guidance": "**Tip:** Photos are excellent evidence for incident investigations and can help prevent similar occurrences."
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis could be a Safety Data Sheet or important safety documentation. Let me help you get it into the right place.",
                "type": "file_upload",
                "actions": [
                    {
                        "text": "📋 Add to SDS Library",
                        "action": "navigate",
                        "url": "/sds/upload"
                    },
                    {
                        "text": "📎 Use for Incident Documentation",
                        "action": "navigate",
                        "url": "/incidents/new"
                    },
                    {
                        "text": "📚 Add to Document Library",
                        "action": "navigate",
                        "url": "/dashboard"
                    }
                ],
                "guidance": "**Tip:** If this is an SDS, uploading it to our library enables AI-powered Q&A and easy searching."
            }
    
    # Enhanced intent detection for fallback
    if any(word in message_lower for word in ["incident", "accident", "injury", "hurt", "damage", "spill"]):
        return {
            "message": "🚨 **I'll help you report this incident properly.**\n\nProper incident reporting helps us learn and prevent future occurrences. Every detail matters for effective investigation.",
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
                    "text": "🌊 Environmental/Spill",
                    "action": "navigate",
                    "url": "/incidents/new?type=environmental"
                },
                {
                    "text": "💔 Property Damage",
                    "action": "navigate",
                    "url": "/incidents/new?type=property"
                },
                {
                    "text": "⚠️ Near Miss",
                    "action": "navigate",
                    "url": "/incidents/new?type=near_miss"
                }
            ],
            "quick_replies": [
                "Someone was injured",
                "There was property damage",
                "Chemical spill occurred", 
                "It was a near miss",
                "Vehicle accident"
            ],
            "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first. Report to the system after ensuring everyone's safety."
        }
    
    elif any(word in message_lower for word in ["safety", "concern", "unsafe", "hazard", "dangerous", "worry"]):
        return {
            "message": "🛡️ **Thank you for speaking up about safety!**\n\nEvery safety observation helps create a safer workplace. Your voice matters and helps protect everyone.",
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
                    "text": "🎯 Safety Recognition",
                    "action": "navigate",
                    "url": "/safety-concerns/new?type=recognition"
                },
                {
                    "text": "📋 View All Concerns",
                    "action": "navigate",
                    "url": "/safety-concerns"
                }
            ],
            "quick_replies": [
                "I observed something unsafe",
                "There's a potential hazard",
                "I want to report anonymously",
                "Someone deserves recognition"
            ],
            "guidance": "**All reports are taken seriously and investigated promptly. Anonymous reports are completely confidential.**"
        }
    
    elif any(word in message_lower for word in ["risk", "assess", "evaluate", "likelihood", "severity"]):
        return {
            "message": "📊 **I'll help you with risk assessment.**\n\nOur system uses the Event Risk Classification (ERC) matrix to evaluate both likelihood and severity across multiple impact categories.",
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
                },
                {
                    "text": "📚 Learn About ERC Matrix",
                    "action": "navigate",
                    "url": "/risk/guide"
                }
            ],
            "quick_replies": [
                "Start a new assessment",
                "Show me existing risks",
                "How does the ERC matrix work?",
                "What are severity categories?"
            ],
            "guidance": "**The ERC matrix evaluates likelihood (0-10) and severity across People, Environment, Cost, Reputation, and Legal categories.**"
        }
    
    elif any(word in message_lower for word in ["capa", "corrective", "preventive", "action", "follow", "fix"]):
        return {
            "message": "🔄 **I'll help you with Corrective and Preventive Actions (CAPA).**\n\nCAPAs ensure we learn from incidents and continuously improve our safety performance through systematic problem-solving.",
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
                    "text": "📋 My Assigned CAPAs",
                    "action": "navigate",
                    "url": "/capa/assigned"
                },
                {
                    "text": "⏰ View Overdue Items",
                    "action": "navigate",
                    "url": "/capa?filter=overdue"
                }
            ],
            "quick_replies": [
                "Create a corrective action",
                "Create a preventive action",
                "Show me my CAPAs",
                "What's overdue?"
            ],
            "guidance": "**Corrective Actions** fix existing problems. **Preventive Actions** prevent future issues. Both are essential for continuous improvement."
        }
    
    elif any(word in message_lower for word in ["sds", "safety data sheet", "chemical", "material", "msds"]):
        return {
            "message": "📄 **I'll help you find Safety Data Sheets and chemical information.**\n\nOur SDS library includes AI-powered chat functionality - you can ask questions about specific chemicals and get instant answers with citations.",
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
                },
                {
                    "text": "💬 Chat with SDS",
                    "action": "navigate",
                    "url": "/sds"
                },
                {
                    "text": "🏷️ Generate QR Codes",
                    "action": "navigate",
                    "url": "/sds/qr-generator"
                }
            ],
            "quick_replies": [
                "Search for acetone",
                "Search for ammonia",
                "Upload a new SDS document",
                "Show me all chemicals"
            ],
            "guidance": "**Pro tip:** Upload PDFs to enable AI chat, or scan QR codes on containers for instant SDS access."
        }
    
    elif any(word in message_lower for word in ["audit", "inspection", "checklist", "compliance", "check"]):
        return {
            "message": "🔍 **I'll help you with audits and inspections.**\n\nRegular audits help ensure compliance and identify improvement opportunities before they become incidents.",
            "type": "audit_help",
            "actions": [
                {
                    "text": "🎯 Start New Audit",
                    "action": "navigate",
                    "url": "/audits/new"
                },
                {
                    "text": "📅 Scheduled Audits",
                    "action": "navigate",
                    "url": "/audits/schedule"
                },
                {
                    "text": "📊 Audit Dashboard",
                    "action": "navigate",
                    "url": "/audits/dashboard"
                },
                {
                    "text": "📋 Audit History",
                    "action": "navigate",
                    "url": "/audits"
                }
            ],
            "quick_replies": [
                "Start safety walkthrough",
                "Chemical management audit",
                "Equipment safety check",
                "What's due for inspection?"
            ]
        }
    
    elif any(word in message_lower for word in ["dashboard", "overview", "status", "urgent", "attention", "summary"]):
        try:
            # Try to get actual stats
            from services.dashboard_stats import get_dashboard_statistics
            stats = get_dashboard_statistics()
            
            urgent_items = []
            if stats.get("incidents", {}).get("open", 0) > 0:
                urgent_items.append(f"**{stats['incidents']['open']} open incidents** need attention")
            if stats.get("capas", {}).get("overdue", 0) > 0:
                urgent_items.append(f"**{stats['capas']['overdue']} overdue CAPAs** require action")
            if stats.get("safety_concerns", {}).get("open", 0) > 0:
                urgent_items.append(f"**{stats['safety_concerns']['open']} safety concerns** awaiting response")
            
            urgent_summary = "\n\n**Items requiring attention:**\n• " + "\n• ".join(urgent_items) if urgent_items else "\n\n✅ **All systems running smoothly!**"
            
            return {
                "message": f"📊 **EHS System Overview**{urgent_summary}\n\nLet me direct you to the areas that need your attention.",
                "type": "dashboard_help",
                "actions": [
                    {
                        "text": "📊 Full Dashboard",
                        "action": "navigate",
                        "url": "/dashboard"
                    },
                    {
                        "text": "📋 Open Incidents",
                        "action": "navigate",
                        "url": "/incidents?filter=open"
                    },
                    {
                        "text": "🔄 Overdue CAPAs",
                        "action": "navigate",
                        "url": "/capa?filter=overdue"
                    },
                    {
                        "text": "🛡️ Safety Concerns",
                        "action": "navigate",
                        "url": "/safety-concerns"
                    }
                ],
                "stats": stats
            }
        except:
            return {
                "message": "📊 **EHS System Overview**\n\nI can help you navigate to different areas of the system to check status and urgent items.",
                "type": "dashboard_help",
                "actions": [
                    {
                        "text": "📊 View Dashboard",
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
                    }
                ]
            }
    
    elif any(word in message_lower for word in ["emergency", "911", "fire", "urgent help", "immediate"]):
        return {
            "message": "🚨 **EMERGENCY DETECTED**\n\n**FOR LIFE-THREATENING EMERGENCIES: CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569\n\n**After ensuring everyone's safety, I can help you document this incident.**",
            "type": "emergency",
            "priority": "critical",
            "actions": [
                {
                    "text": "📝 Report Emergency Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency"
                },
                {
                    "text": "🚨 Site Emergency Procedures",
                    "action": "navigate",
                    "url": "/procedures/emergency"
                }
            ],
            "guidance": "**REMEMBER:** Life safety comes first. Only use this system AFTER addressing immediate emergency needs."
        }
    
    elif any(word in message_lower for word in ["help", "guide", "how", "what can you do", "assist"]):
        return {
            "message": "🤖 **I'm your Smart EHS Assistant!**\n\nI can help you navigate and work with all aspects of our EHS management system:\n\n🚨 **Safety Reporting**\n• Report incidents and accidents\n• Submit safety concerns and observations\n• Document near-miss events\n\n📊 **Risk & Compliance**\n• Conduct risk assessments\n• Manage corrective actions (CAPAs)\n• Track audit findings\n\n📚 **Information & Resources**\n• Find safety data sheets\n• Search system documentation\n• Get guidance on procedures\n\n**What would you like to work on?**",
            "type": "help_menu",
            "actions": [
                {
                    "text": "🚨 Report Something",
                    "action": "continue_conversation", 
                    "message": "I need to report an incident or safety concern"
                },
                {
                    "text": "📊 Risk Assessment",
                    "action": "navigate",
                    "url": "/risk/assess"
                },
                {
                    "text": "📄 Find Information",
                    "action": "continue_conversation",
                    "message": "I need to find safety data sheets or documentation"
                },
                {
                    "text": "📈 View Status",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern", 
                "Find SDS",
                "Risk assessment",
                "What's urgent?",
                "Show me around"
            ]
        }
    
    else:
        # Default comprehensive response
        return {
            "message": "🤖 **I'm here to help with your EHS needs!**\n\nI can assist you with:\n\n• **Reporting incidents** and safety concerns\n• **Risk assessments** and safety analysis\n• **Finding information** like safety data sheets\n• **Managing CAPAs** and corrective actions\n• **System navigation** and urgent items\n\nJust tell me what you need in plain language, or choose from the options below.",
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
                },
                {
                    "text": "🔄 CAPAs",
                    "action": "navigate",
                    "url": "/capa"
                },
                {
                    "text": "🎯 Risk Assessment",
                    "action": "navigate",
                    "url": "/risk/assess"
                }
            ],
            "quick_replies": [
                "Report an incident",
                "Safety concern",
                "Risk assessment",
                "Find SDS", 
                "What's urgent?",
                "Help me get started"
            ]
        }

# Enhanced routes/incidents.py - Integration with chatbot and enhanced validation
from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, abort, jsonify
from services.incident_validator import (
    REQUIRED_BY_TYPE, compute_completeness, validate_record, 
    generate_scoring_and_capas
)
from services.pdf import build_incident_pdf

# Update the incidents route to include chatbot integration
@chatbot_bp.route("/incidents/chat-assist", methods=["POST"])
def incident_chat_assist():
    """Assist with incident reporting through chat interface"""
    if not CHATBOT_AVAILABLE:
        return jsonify({"error": "Chat assistance not available"}), 503
    
    try:
        data = request.get_json()
        incident_type = data.get("incident_type")
        current_data = data.get("current_data", {})
        
        # Switch chatbot to incident mode
        chatbot.current_mode = "incident"
        chatbot.current_context = {"incident_type": incident_type}
        
        # Generate next question based on current data
        response = chatbot.continue_slot_filling("")
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/incidents/<incident_id>/enhance", methods=["POST"])
def enhance_incident_with_ai():
    """Enhance incident with AI-generated scoring and CAPAs"""
    try:
        # Load incident data
        incidents_file = Path("data/incidents.json")
        if not incidents_file.exists():
            return jsonify({"error": "No incidents found"}), 404
        
        incidents = json.loads(incidents_file.read_text())
        incident = incidents.get(incident_id)
        
        if not incident:
            return jsonify({"error": "Incident not found"}), 404
        
        # Generate enhanced analysis
        enhancement = generate_scoring_and_capas(incident)
        
        # Update incident with AI enhancements
        incident["ai_analysis"] = enhancement
        incident["enhanced_at"] = time.time()
        
        # Save updated incident
        incidents[incident_id] = incident
        incidents_file.write_text(json.dumps(incidents, indent=2))
        
        return jsonify({
            "status": "enhanced",
            "analysis": enhancement,
            "message": "Incident enhanced with AI analysis"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Enhanced SDS routes with chat integration
@chatbot_bp.route("/sds/<sds_id>/chat-session", methods=["POST"])
def sds_chat_session():
    """Create or continue SDS chat session"""
    try:
        from services.sds_ingest import SDSChatSystem
        
        data = request.get_json()
        question = data.get("question", "")
        context = data.get("context", {})
        
        chat_system = SDSChatSystem()
        response = chat_system.chat_with_sds(sds_id, question, context)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chatbot_bp.route("/sds/multi-search", methods=["POST"])
def sds_multi_search():
    """Search across all SDS documents"""
    try:
        from services.sds_ingest import search_across_all_sds
        
        data = request.get_json()
        query = data.get("query", "")
        limit = data.get("limit", 5)
        
        results = search_across_all_sds(query, limit)
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check and system status
@chatbot_bp.route("/chat/status")
def chat_status():
    """Get chatbot system status"""
    status = {
        "chatbot_available": CHATBOT_AVAILABLE,
        "current_mode": chatbot.current_mode if CHATBOT_AVAILABLE else "unavailable",
        "conversation_count": len(chatbot.conversation_history) if CHATBOT_AVAILABLE else 0,
        "features": {
            "file_upload": True,
            "intent_classification": CHATBOT_AVAILABLE,
            "slot_filling": CHATBOT_AVAILABLE,
            "risk_scoring": True,
            "sds_chat": True,
            "capa_generation": True
        }
    }
    
    return jsonify(status)
