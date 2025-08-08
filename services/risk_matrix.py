# Enhanced EHS System with AI Chatbot and Full Module Support

# New file: services/risk_matrix.py
LIKELIHOOD_SCALE = {
    0: {"label": "Impossible", "description": "The event cannot happen under current design or controls"},
    2: {"label": "Rare", "description": "Extremely unlikely but theoretically possible (once in 10+ years)"},
    4: {"label": "Unlikely", "description": "Could happen in exceptional cases (once every 5–10 years)"},
    6: {"label": "Possible", "description": "Might occur occasionally under abnormal conditions (once every 1–5 years)"},
    8: {"label": "Likely", "description": "Occurs regularly or has been documented (multiple times per year)"},
    10: {"label": "Almost Certain", "description": "Expected to happen frequently (monthly or more)"}
}

SEVERITY_SCALE = {
    "people": {
        0: "No injury or risk of harm",
        2: "First aid only; no lost time",
        4: "Medical treatment; lost time injury (LTI), no hospitalization",
        6: "Serious injury; hospitalization, restricted duty >3 days",
        8: "Permanent disability, amputation, serious head/spine injury",
        10: "Fatality or multiple severe injuries"
    },
    "environment": {
        0: "No release or environmental impact",
        2: "Minor release, fully contained, no reporting needed",
        4: "Moderate release, requires internal reporting",
        6: "Reportable spill; affects stormwater, air, or soil; TCEQ/EPA notification",
        8: "Major spill; spread beyond site boundary, public/environmental impact",
        10: "Catastrophic event; large-scale contamination or cleanup needed"
    },
    "cost": {
        0: "No damage or cost",
        2: "Minor damage; <$1,000",
        4: "$1,000–$10,000; minor repair to AEV or equipment",
        6: "$10,000–$100,000; significant repair or downtime",
        8: "Critical asset loss; one AEV out of service long-term",
        10: ">$100,000 damage or liability claim"
    },
    "reputation": {
        0: "No impact to reputation",
        2: "Internally noticed only; no client or public awareness",
        4: "AVOMO client concern raised; issue handled proactively",
        6: "Uber or Waymo formally logs concern, requires follow-up",
        8: "Incident reaches media or affects corporate partnerships",
        10: "Public crisis; loss of contract or long-term brand damage"
    },
    "legal": {
        0: "Fully compliant; no issue",
        2: "Minor internal policy deviation; corrected on site",
        4: "Potential OSHA or EPA non-compliance; not reportable yet",
        6: "Reportable violation; citation risk or official notice",
        8: "Fines or penalties issued; corrective action required",
        10: "Legal action, shutdown, or major lawsuit; significant regulatory breach"
    }
}

def calculate_risk_score(likelihood, severity_scores):
    """Calculate overall risk score using the ERC methodology"""
    max_severity = max(severity_scores.values()) if severity_scores else 0
    return likelihood * max_severity

def get_risk_level(risk_score):
    """Determine risk level based on score"""
    if risk_score >= 80:
        return "Critical"
    elif risk_score >= 60:
        return "High" 
    elif risk_score >= 40:
        return "Medium"
    elif risk_score >= 20:
        return "Low"
    else:
        return "Very Low"

# New file: services/ehs_chatbot.py
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class EHSChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}
        
    def process_message(self, user_message: str, user_id: str = None) -> Dict:
        """Process user message and return appropriate response"""
        message = user_message.lower().strip()
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Generate response based on intent
        response = self.generate_response(intent, user_message, user_id)
        
        # Update conversation history
        self.conversation_history.append({
            "user_message": user_message,
            "bot_response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        # Incident reporting keywords
        incident_keywords = ["incident", "accident", "injury", "spill", "collision", "damage", "report incident"]
        
        # Safety concern keywords  
        concern_keywords = ["concern", "unsafe", "hazard", "near miss", "observation", "worry"]
        
        # Risk assessment keywords
        risk_keywords = ["risk", "assess", "likelihood", "severity", "evaluate risk"]
        
        # CAPA keywords
        capa_keywords = ["corrective action", "capa", "follow up", "fix", "prevent"]
        
        # SDS keywords
        sds_keywords = ["sds", "safety data sheet", "chemical", "material", "msds"]
        
        # Audit keywords
        audit_keywords = ["audit", "inspection", "checklist", "compliance"]
        
        # General help/navigation
        help_keywords = ["help", "how", "what", "guide", "assistance"]
        
        if any(keyword in message for keyword in incident_keywords):
            return "incident_reporting"
        elif any(keyword in message for keyword in concern_keywords):
            return "safety_concern"
        elif any(keyword in message for keyword in risk_keywords):
            return "risk_assessment"
        elif any(keyword in message for keyword in capa_keywords):
            return "capa_management"
        elif any(keyword in message for keyword in sds_keywords):
            return "sds_lookup"
        elif any(keyword in message for keyword in audit_keywords):
            return "audit_inspection"
        elif any(keyword in message for keyword in help_keywords):
            return "general_help"
        else:
            return "general_inquiry"
    
    def generate_response(self, intent: str, original_message: str, user_id: str = None) -> Dict:
        """Generate contextual response based on intent"""
        
        if intent == "incident_reporting":
            return {
                "message": "I'll help you report an incident. Let me guide you through the process.",
                "type": "guided_form",
                "actions": [
                    {
                        "text": "Start Incident Report",
                        "action": "navigate",
                        "url": "/incidents/new",
                        "style": "primary"
                    },
                    {
                        "text": "View My Reports", 
                        "action": "navigate",
                        "url": "/incidents",
                        "style": "secondary"
                    }
                ],
                "quick_replies": [
                    "What types of incidents can I report?",
                    "Is this reportable to authorities?",
                    "Can I report anonymously?"
                ],
                "guidance": "You can report injuries, environmental spills, security events, vehicle collisions, property damage, and near misses. All reports are confidential and help improve our safety."
            }
            
        elif intent == "safety_concern":
            return {
                "message": "Thank you for speaking up about a safety concern. Every observation helps keep everyone safe.",
                "type": "guided_form", 
                "actions": [
                    {
                        "text": "Report Safety Concern",
                        "action": "navigate", 
                        "url": "/safety-concerns/new",
                        "style": "primary"
                    },
                    {
                        "text": "Emergency Contacts",
                        "action": "show_emergency_info",
                        "style": "danger"
                    }
                ],
                "quick_replies": [
                    "Is this an emergency?",
                    "What happens after I report?",
                    "How is my privacy protected?"
                ],
                "guidance": "If this is an immediate danger, contact security or call 911. For non-emergency concerns, I'll help you create a safety observation report."
            }
            
        elif intent == "risk_assessment":
            return {
                "message": "I'll help you assess risk using our Event Risk Classification (ERC) matrix. This considers likelihood and severity across 5 categories.",
                "type": "risk_tool",
                "actions": [
                    {
                        "text": "Start Risk Assessment",
                        "action": "navigate",
                        "url": "/risk/assess",
                        "style": "primary"
                    },
                    {
                        "text": "View Risk Register",
                        "action": "navigate", 
                        "url": "/risk/register",
                        "style": "secondary"
                    }
                ],
                "guidance": "Our ERC evaluates likelihood (0-10) and severity across People, Environment, Cost, Reputation, and Legal categories.",
                "risk_info": {
                    "likelihood_scale": LIKELIHOOD_SCALE,
                    "severity_categories": list(SEVERITY_SCALE.keys())
                }
            }
            
        elif intent == "capa_management":
            return {
                "message": "I'll help you with Corrective and Preventive Actions (CAPA). These ensure we learn from incidents and prevent recurrence.",
                "type": "capa_tool",
                "actions": [
                    {
                        "text": "Create CAPA",
                        "action": "navigate",
                        "url": "/capa/new", 
                        "style": "primary"
                    },
                    {
                        "text": "My CAPAs",
                        "action": "navigate",
                        "url": "/capa/assigned",
                        "style": "secondary"
                    },
                    {
                        "text": "CAPA Dashboard",
                        "action": "navigate",
                        "url": "/capa/dashboard",
                        "style": "info"
                    }
                ],
                "quick_replies": [
                    "What's the difference between corrective and preventive?",
                    "How do I track CAPA progress?",
                    "What are SLA requirements?"
                ]
            }
            
        elif intent == "sds_lookup":
            return {
                "message": "I can help you find Safety Data Sheets for chemicals and materials at your site.",
                "type": "sds_tool",
                "actions": [
                    {
                        "text": "Search SDS Library",
                        "action": "navigate",
                        "url": "/sds",
                        "style": "primary"
                    },
                    {
                        "text": "Upload New SDS",
                        "action": "navigate", 
                        "url": "/sds/upload",
                        "style": "secondary"
                    },
                    {
                        "text": "Chat with SDS",
                        "action": "navigate",
                        "url": "/sds",
                        "style": "info",
                        "note": "Ask questions about specific SDS content"
                    }
                ],
                "guidance": "Search by chemical name, product name, or manufacturer. You can also scan QR codes on containers to access SDS quickly."
            }
            
        elif intent == "audit_inspection":
            return {
                "message": "I'll help you with audits and inspections to ensure compliance and identify improvement opportunities.",
                "type": "audit_tool",
                "actions": [
                    {
                        "text": "Start Inspection",
                        "action": "navigate",
                        "url": "/audits/new",
                        "style": "primary"
                    },
                    {
                        "text": "Scheduled Audits",
                        "action": "navigate",
                        "url": "/audits/schedule", 
                        "style": "secondary"
                    },
                    {
                        "text": "Audit History",
                        "action": "navigate",
                        "url": "/audits/history",
                        "style": "info"
                    }
                ],
                "quick_replies": [
                    "What types of inspections are required?",
                    "How often should I audit my area?",
                    "What happens if I find non-compliance?"
                ]
            }
            
        elif intent == "general_help":
            return {
                "message": "I'm your Smart EHS assistant! I can help you with:",
                "type": "menu",
                "menu_items": [
                    "🚨 Report Incidents & Safety Concerns",
                    "📊 Risk Assessment & Management", 
                    "✅ Corrective Actions (CAPA)",
                    "📋 Safety Data Sheets (SDS)",
                    "🔍 Audits & Inspections",
                    "📈 Dashboards & Analytics",
                    "📚 Document Management",
                    "👥 Contractor Management"
                ],
                "quick_replies": [
                    "Show me the dashboard",
                    "What's my role in the system?",
                    "Emergency contacts"
                ]
            }
            
        else:
            return {
                "message": "I understand you're asking about our EHS system. Could you be more specific about what you need help with?",
                "type": "clarification",
                "quick_replies": [
                    "Report an incident",
                    "Safety concern", 
                    "Find SDS",
                    "Risk assessment",
                    "Show main menu"
                ]
            }

# New file: routes/chatbot.py
from flask import Blueprint, request, jsonify, render_template
from services.ehs_chatbot import EHSChatbot

chatbot_bp = Blueprint("chatbot", __name__)
chatbot = EHSChatbot()

@chatbot_bp.route("/chat", methods=["GET", "POST"])
def chat_interface():
    if request.method == "GET":
        return render_template("chatbot.html")
    
    data = request.get_json()
    user_message = data.get("message", "")
    user_id = data.get("user_id")
    
    response = chatbot.process_message(user_message, user_id)
    
    return jsonify(response)

@chatbot_bp.route("/chat/history")
def chat_history():
    return jsonify(chatbot.conversation_history[-20:])  # Last 20 messages

# New file: services/capa_manager.py
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class CAPAManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.capa_file = self.data_dir / "capa.json"
        
    def load_capas(self) -> Dict:
        if self.capa_file.exists():
            return json.loads(self.capa_file.read_text())
        return {}
    
    def save_capas(self, capas: Dict):
        self.data_dir.mkdir(exist_ok=True)
        self.capa_file.write_text(json.dumps(capas, indent=2))
    
    def create_capa(self, data: Dict) -> str:
        capas = self.load_capas()
        capa_id = str(int(time.time() * 1000))
        
        capa = {
            "id": capa_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "type": data.get("type", "corrective"),  # corrective, preventive
            "source": data.get("source", "manual"),  # manual, incident, audit, risk
            "source_id": data.get("source_id"),
            "assignee": data.get("assignee", ""),
            "due_date": data.get("due_date", ""),
            "priority": data.get("priority", "medium"),  # low, medium, high, critical
            "status": "open",
            "created_date": datetime.now().isoformat(),
            "created_by": data.get("created_by", ""),
            "updates": [],
            "risk_level": data.get("risk_level", "medium")
        }
        
        capas[capa_id] = capa
        self.save_capas(capas)
        return capa_id
    
    def update_capa(self, capa_id: str, update_data: Dict) -> bool:
        capas = self.load_capas()
        if capa_id not in capas:
            return False
            
        capa = capas[capa_id]
        
        # Add update to history
        update = {
            "timestamp": datetime.now().isoformat(),
            "user": update_data.get("updated_by", ""),
            "comment": update_data.get("comment", ""),
            "status_change": update_data.get("status") != capa.get("status")
        }
        
        capa["updates"].append(update)
        
        # Update fields
        for key, value in update_data.items():
            if key in ["status", "assignee", "due_date", "priority"]:
                capa[key] = value
                
        capas[capa_id] = capa
        self.save_capas(capas)
        return True
    
    def get_overdue_capas(self) -> List[Dict]:
        capas = self.load_capas()
        overdue = []
        today = datetime.now().date()
        
        for capa in capas.values():
            if capa["status"] in ["open", "in_progress"]:
                try:
                    due_date = datetime.fromisoformat(capa["due_date"]).date()
                    if due_date < today:
                        overdue.append(capa)
                except (ValueError, TypeError):
                    continue
                    
        return overdue

# Enhanced app.py to include all modules
def create_app():
    ensure_dirs()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    
    # Register all blueprints
    app.register_blueprint(sds_bp, url_prefix="/sds")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")
    app.register_blueprint(chatbot_bp, url_prefix="/")
    
    # Additional blueprints for new modules
    # app.register_blueprint(capa_bp, url_prefix="/capa")
    # app.register_blueprint(risk_bp, url_prefix="/risk") 
    # app.register_blueprint(audit_bp, url_prefix="/audits")
    # app.register_blueprint(safety_concerns_bp, url_prefix="/safety-concerns")

    @app.route("/")
    def index():
        return render_template("dashboard.html")

    return app
