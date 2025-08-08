# services/ehs_chatbot.py - Enhanced AI Chatbot for EHS Management
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class EHSChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}
        self.emergency_keywords = [
            "emergency", "fire", "injury", "spill", "evacuation", 
            "911", "help", "urgent", "immediate", "danger"
        ]
        
    def process_message(self, user_message: str, user_id: str = None) -> Dict:
        """Process user message and return appropriate response"""
        message = user_message.lower().strip()
        
        # Check for emergency first
        if self.is_emergency(message):
            return self.handle_emergency()
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Generate response based on intent
        response = self.generate_response(intent, user_message, user_id)
        
        # Update conversation history
        self.conversation_history.append({
            "user_message": user_message,
            "bot_response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        })
        
        return response
    
    def is_emergency(self, message: str) -> bool:
        """Check if message indicates an emergency situation"""
        return any(keyword in message for keyword in self.emergency_keywords)
    
    def handle_emergency(self) -> Dict:
        """Handle emergency situations with immediate response"""
        return {
            "message": "🚨 EMERGENCY DETECTED 🚨",
            "type": "emergency",
            "priority": "critical",
            "emergency_info": {
                "immediate_actions": [
                    "If life-threatening: Call 911 immediately",
                    "For site emergency: Call (555) 123-4567",
                    "Security: (555) 123-4568",
                    "EHS Hotline: (555) 123-4569"
                ],
                "spill_response": "Environmental Spill: (555) 123-4570"
            },
            "actions": [
                {
                    "text": "Report Emergency Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency",
                    "style": "danger"
                },
                {
                    "text": "View Emergency Procedures",
                    "action": "navigate",
                    "url": "/emergency-procedures",
                    "style": "warning"
                }
            ],
            "guidance": "If this is a life-threatening emergency, stop reading and call 911 now. For other emergencies, use the contacts above and report the incident through our system."
        }
    
    def detect_intent(self, message: str) -> str:
        """Enhanced intent detection with better keyword matching"""
        
        # Incident reporting patterns
        incident_patterns = [
            r"(report|create|new).*(incident|accident|injury)",
            r"(accident|injury|spill|collision|damage).*happened",
            r"need to report",
            r"incident.*report",
            r"someone.*hurt",
            r"equipment.*damaged"
        ]
        
        # Safety concern patterns
        concern_patterns = [
            r"safety.*concern",
            r"unsafe.*condition",
            r"near.*miss",
            r"safety.*observation",
            r"hazard.*identified",
            r"something.*unsafe",
            r"worried.*about"
        ]
        
        # Risk assessment patterns
        risk_patterns = [
            r"risk.*assessment",
            r"evaluate.*risk",
            r"risk.*matrix",
            r"likelihood.*severity",
            r"erc.*assessment",
            r"calculate.*risk"
        ]
        
        # CAPA patterns
        capa_patterns = [
            r"corrective.*action",
            r"preventive.*action",
            r"capa.*management",
            r"follow.*up",
            r"action.*plan",
            r"fix.*problem"
        ]
        
        # SDS patterns
        sds_patterns = [
            r"safety.*data.*sheet",
            r"sds.*lookup",
            r"chemical.*information",
            r"material.*safety",
            r"msds.*search",
            r"find.*sds"
        ]
        
        # Audit patterns
        audit_patterns = [
            r"audit.*checklist",
            r"inspection.*form",
            r"compliance.*check",
            r"safety.*inspection",
            r"audit.*template"
        ]
        
        # Contractor patterns
        contractor_patterns = [
            r"contractor.*safety",
            r"visitor.*requirements",
            r"vendor.*access",
            r"site.*orientation",
            r"contractor.*training"
        ]
        
        # Document patterns
        document_patterns = [
            r"document.*management",
            r"policy.*search",
            r"procedure.*lookup",
            r"find.*document",
            r"document.*control"
        ]
        
        # Check patterns in order of specificity
        pattern_map = [
            (incident_patterns, "incident_reporting"),
            (concern_patterns, "safety_concern"),
            (risk_patterns, "risk_assessment"),
            (capa_patterns, "capa_management"),
            (sds_patterns, "sds_lookup"),
            (audit_patterns, "audit_inspection"),
            (contractor_patterns, "contractor_management"),
            (document_patterns, "document_management")
        ]
        
        for patterns, intent in pattern_map:
            if any(re.search(pattern, message) for pattern in patterns):
                return intent
        
        # Simple keyword fallback
        if any(word in message for word in ["help", "guide", "how", "what", "menu"]):
            return "general_help"
        
        return "general_inquiry"
    
    def generate_response(self, intent: str, original_message: str, user_id: str = None) -> Dict:
        """Generate contextual response based on intent"""
        
        responses = {
            "incident_reporting": self.get_incident_response(),
            "safety_concern": self.get_safety_concern_response(),
            "risk_assessment": self.get_risk_assessment_response(),
            "capa_management": self.get_capa_response(),
            "sds_lookup": self.get_sds_response(),
            "audit_inspection": self.get_audit_response(),
            "contractor_management": self.get_contractor_response(),
            "document_management": self.get_document_response(),
            "general_help": self.get_help_response(),
            "general_inquiry": self.get_general_response(original_message)
        }
        
        return responses.get(intent, self.get_general_response(original_message))
    
    def get_incident_response(self) -> Dict:
        return {
            "message": "I'll help you report an incident. Our system handles all types of workplace incidents with automated workflows.",
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
                },
                {
                    "text": "Emergency Report",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency", 
                    "style": "danger"
                }
            ],
            "quick_replies": [
                "What types of incidents should I report?",
                "Is this reportable to authorities?",
                "Can I report anonymously?",
                "How long do I have to report?"
            ],
            "guidance": "Report all incidents within 24 hours. Include injuries, near misses, equipment damage, spills, and security events. All reports are confidential and help improve our safety culture."
        }
    
    def get_safety_concern_response(self) -> Dict:
        return {
            "message": "Thank you for speaking up! Safety concerns and observations are vital to maintaining a safe workplace.",
            "type": "safety_tool",
            "actions": [
                {
                    "text": "Report Safety Concern",
                    "action": "navigate",
                    "url": "/safety-concerns/new",
                    "style": "warning"
                },
                {
                    "text": "Submit Recognition",
                    "action": "navigate",
                    "url": "/safety-concerns/new?type=recognition",
                    "style": "success"
                },
                {
                    "text": "View All Concerns",
                    "action": "navigate",
                    "url": "/safety-concerns",
                    "style": "secondary"
                }
            ],
            "quick_replies": [
                "What happens after I report?",
                "Can I report anonymously?",
                "How quickly will this be addressed?",
                "What if I see unsafe behavior?"
            ],
            "guidance": "All safety concerns receive prompt attention. Anonymous reports are welcome, and we follow up within 24 hours on all submissions."
        }
    
    def get_risk_assessment_response(self) -> Dict:
        return {
            "message": "I'll guide you through our Event Risk Classification (ERC) process. This evaluates likelihood and impact across five critical areas.",
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
                    "style": "info"
                },
                {
                    "text": "Risk Matrix Guide",
                    "action": "navigate",
                    "url": "/risk/guide",
                    "style": "secondary"
                }
            ],
            "risk_info": {
                "categories": ["People", "Environment", "Cost", "Reputation", "Legal"],
                "likelihood_range": "0-10 scale (Impossible to Almost Certain)",
                "severity_range": "0-10 scale per category"
            },
            "guidance": "Our 3D risk matrix considers likelihood (0-10) and severity across People, Environment, Cost, Reputation, and Legal impact categories."
        }
    
    def get_capa_response(self) -> Dict:
        return {
            "message": "CAPA (Corrective and Preventive Actions) ensures we learn from incidents and prevent recurrence through systematic improvement.",
            "type": "capa_tool", 
            "actions": [
                {
                    "text": "Create CAPA",
                    "action": "navigate",
                    "url": "/capa/new",
                    "style": "primary"
                },
                {
                    "text": "My Assigned CAPAs", 
                    "action": "navigate",
                    "url": "/capa/assigned",
                    "style": "warning"
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
                "What are the SLA requirements?",
                "Who can assign CAPAs?"
            ],
            "guidance": "Corrective actions fix current problems, while preventive actions stop future issues. All CAPAs have defined SLAs and require evidence of completion."
        }
    
    def get_sds_response(self) -> Dict:
        return {
            "message": "I can help you find Safety Data Sheets and answer questions about chemical hazards and handling procedures.",
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
                    "style": "success"
                },
                {
                    "text": "SDS Chat Assistant",
                    "action": "navigate",
                    "url": "/sds",
                    "style": "info"
                }
            ],
            "quick_replies": [
                "How do I find SDS for a specific chemical?",
                "Can I scan QR codes to access SDS?",
                "What PPE is required for this chemical?",
                "How often are SDS updated?"
            ],
            "guidance": "Search by product name, manufacturer, or chemical name. QR codes on containers provide instant access. AI chat helps interpret complex safety information."
        }
    
    def get_audit_response(self) -> Dict:
        return {
            "message": "Our audit system provides structured inspections with automated scoring and CAPA generation for findings.",
            "type": "audit_tool",
            "actions": [
                {
                    "text": "Start New Audit",
                    "action": "navigate",
                    "url": "/audits/new", 
                    "style": "primary"
                },
                {
                    "text": "Scheduled Audits",
                    "action": "navigate",
                    "url": "/audits/scheduled",
                    "style": "warning"
                },
                {
                    "text": "Audit Templates",
                    "action": "navigate", 
                    "url": "/audits/templates",
                    "style": "secondary"
                }
            ],
            "quick_replies": [
                "What audit templates are available?",
                "How is audit scoring calculated?", 
                "Who can conduct audits?",
                "How often should I audit my area?"
            ],
            "guidance": "Choose from pre-built templates or create custom checklists. Findings automatically generate CAPAs with assigned responsibilities and due dates."
        }
    
    def get_contractor_response(self) -> Dict:
        return {
            "message": "Our contractor management system ensures all vendors meet safety requirements before accessing your facilities.",
            "type": "contractor_tool",
            "actions": [
                {
                    "text": "Register New Contractor",
                    "action": "navigate",
                    "url": "/contractors/register",
                    "style": "primary"
                },
                {
                    "text": "Visitor Check-in",
                    "action": "navigate",
                    "url": "/visitors/checkin",
                    "style": "success"
                },
                {
                    "text": "Safety Orientation",
                    "action": "navigate",
                    "url": "/contractors/orientation", 
                    "style": "info"
                }
            ],
            "quick_replies": [
                "What documents do contractors need?",
                "How long is safety training valid?",
                "Can contractors work alone?",
                "What are visitor requirements?"
            ],
            "guidance": "All contractors must complete safety orientation, provide insurance, and demonstrate competency before accessing work areas."
        }
    
    def get_document_response(self) -> Dict:
        return {
            "message": "Access policies, procedures, and forms through our document management system with version control and approval workflows.",
            "type": "document_tool",
            "actions": [
                {
                    "text": "Search Documents",
                    "action": "navigate",
                    "url": "/documents/search",
                    "style": "primary"
                },
                {
                    "text": "Policy Library",
                    "action": "navigate",
                    "url": "/documents/policies",
                    "style": "info"
                },
                {
                    "text": "Forms & Templates",
                    "action": "navigate",
                    "url": "/documents/forms",
                    "style": "secondary"
                }
            ],
            "guidance": "All documents include version history, approval status, and automatic notifications for updates. Use search or browse by category."
        }
    
    def get_help_response(self) -> Dict:
        return {
            "message": "I'm your Smart EHS Assistant! I can help you navigate all aspects of environmental, health, and safety management.",
            "type": "menu",
            "menu_items": [
                {
                    "icon": "🚨", 
                    "title": "Incident Reporting",
                    "description": "Report injuries, spills, near misses, and other incidents",
                    "action": "sendMessage('Report an incident')"
                },
                {
                    "icon": "🛡️",
                    "title": "Safety Concerns", 
                    "description": "Submit observations and safety concerns",
                    "action": "sendMessage('Safety concern')"
                },
                {
                    "icon": "📊",
                    "title": "Risk Assessment",
                    "description": "Evaluate risks using our ERC matrix",
                    "action": "sendMessage('Risk assessment')"
                },
                {
                    "icon": "✅", 
                    "title": "Corrective Actions",
                    "description": "Manage CAPA workflows and tracking",
                    "action": "sendMessage('Create CAPA')"
                },
                {
                    "icon": "📋",
                    "title": "Safety Data Sheets",
                    "description": "Search SDS library and get chemical info",
                    "action": "sendMessage('Find SDS')"
                },
                {
                    "icon": "🔍",
                    "title": "Audits & Inspections", 
                    "description": "Conduct safety audits and inspections",
                    "action": "sendMessage('Start audit')"
                }
            ],
            "quick_replies": [
                "Show dashboard",
                "Emergency contacts",
                "What's new in EHS?",
                "Training schedule"
            ]
        }
    
    def get_general_response(self, message: str) -> Dict:
        return {
            "message": f"I understand you're asking about '{message}'. Could you be more specific about what you need help with?",
            "type": "clarification", 
            "suggestions": [
                "Try asking: 'How do I report an incident?'",
                "Or: 'I need to find an SDS for acetone'",
                "Or: 'Show me safety procedures'"
            ],
            "quick_replies": [
                "Report incident",
                "Safety concern",
                "Find SDS", 
                "Risk assessment",
                "Show main menu"
            ]
        }
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of recent conversation for context"""
        recent_messages = self.conversation_history[-5:]
        intents = [msg["intent"] for msg in recent_messages]
        
        return {
            "recent_intents": intents,
            "message_count": len(self.conversation_history),
            "common_topics": self._get_common_topics(intents)
        }
    
    def _get_common_topics(self, intents: List[str]) -> List[str]:
        """Identify common topics in conversation"""
        topic_map = {
            "incident_reporting": "incidents",
            "safety_concern": "safety",
            "risk_assessment": "risk", 
            "capa_management": "improvement",
            "sds_lookup": "chemicals"
        }
        
        topics = [topic_map.get(intent, "general") for intent in intents]
        return list(set(topics))
