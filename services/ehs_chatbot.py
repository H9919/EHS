# services/ehs_chatbot.py - Fixed indentation errors
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class EHSChatbot:
    def __init__(self):
        self.conversation_history = []
        
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Main message processing - this is the core intelligence"""
        message = user_message.lower().strip()
        context = context or {}
        
        # Handle file uploads first
        uploaded_file = context.get("uploaded_file")
        if uploaded_file:
            return self.handle_file_upload(user_message, uploaded_file)
        
        # Emergency detection
        if self.is_emergency(message):
            return self.handle_emergency()
        
        # Smart intent detection
        intent = self.detect_intent(message)
        
        # Generate intelligent response
        response = self.generate_smart_response(intent, user_message, context)
        
        # Store conversation
        self.conversation_history.append({
            "user": user_message,
            "bot": response.get("message", ""),
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def detect_intent(self, message: str) -> str:
        """Smart intent detection based on keywords and patterns"""
        
        # Incident reporting patterns
        incident_patterns = [
            r"report.*incident", r"incident.*report", r"workplace.*incident",
            r"accident", r"injury", r"hurt", r"damaged", r"spill", r"collision",
            r"emergency.*happened", r"something.*happened", r"need.*report.*incident"
        ]
        
        # Safety concern patterns  
        concern_patterns = [
            r"safety.*concern", r"unsafe.*condition", r"hazard", r"dangerous",
            r"near.*miss", r"almost.*accident", r"safety.*issue", r"concern.*about",
            r"worried.*about", r"observed.*unsafe", r"potential.*danger"
        ]
        
        # Risk assessment patterns
        risk_patterns = [
            r"risk.*assessment", r"evaluate.*risk", r"risk.*analysis",
            r"how.*risky", r"what.*risk", r"assess.*risk", r"risk.*level"
        ]
        
        # CAPA patterns
        capa_patterns = [
            r"corrective.*action", r"preventive.*action", r"capa",
            r"fix.*problem", r"prevent.*future", r"action.*plan", r"follow.*up"
        ]
        
        # SDS patterns
        sds_patterns = [
            r"safety.*data.*sheet", r"sds", r"chemical.*info", r"material.*safety",
            r"find.*chemical", r"lookup.*chemical", r"chemical.*safety"
        ]
        
        # Dashboard/overview patterns
        dashboard_patterns = [
            r"overview", r"dashboard", r"status", r"what.*urgent", r"what.*needs.*attention",
            r"summary", r"what.*overdue", r"priorities", r"what.*should.*do"
        ]
        
        # Help patterns
        help_patterns = [
            r"help", r"how.*do", r"what.*can.*you", r"guide.*me", r"assist",
            r"don't.*know", r"confused", r"explain", r"show.*me"
        ]
        
        # Check patterns in order of specificity
        for pattern in incident_patterns:
            if re.search(pattern, message):
                return "incident_reporting"
                
        for pattern in concern_patterns:
            if re.search(pattern, message):
                return "safety_concern"
                
        for pattern in risk_patterns:
            if re.search(pattern, message):
                return "risk_assessment"
                
        for pattern in capa_patterns:
            if re.search(pattern, message):
                return "capa_management"
                
        for pattern in sds_patterns:
            if re.search(pattern, message):
                return "sds_lookup"
                
        for pattern in dashboard_patterns:
            if re.search(pattern, message):
                return "dashboard_overview"
                
        for pattern in help_patterns:
            if re.search(pattern, message):
                return "help_request"
        
        # Default fallback
        return "general_inquiry"
    
    def generate_smart_response(self, intent: str, original_message: str, context: Dict) -> Dict:
        """Generate intelligent responses based on detected intent"""
        
        if intent == "incident_reporting":
            return {
                "message": "🚨 **I'll help you report a workplace incident immediately.**\n\nTo ensure we capture all necessary details for the investigation, I'll guide you through our incident reporting process step by step.\n\n**What type of incident occurred?**",
                "type": "incident_guide",
                "actions": [
                    {
                        "text": "🩹 Injury/Medical",
                        "action": "navigate",
                        "url": "/incidents/new?type=injury"
                    },
                    {
                        "text": "🚗 Vehicle/Equipment",
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
                    },
                    {
                        "text": "📝 Other Incident",
                        "action": "navigate",
                        "url": "/incidents/new"
                    }
                ],
                "quick_replies": [
                    "Someone was injured",
                    "There was property damage", 
                    "It was a near miss",
                    "Environmental spill occurred"
                ],
                "guidance": "**Remember:** If anyone needs immediate medical attention, call 911 first. Report to the system after ensuring everyone's safety."
            }
            
        elif intent == "safety_concern":
            return {
                "message": "🛡️ **Thank you for speaking up about a safety concern!**\n\nEvery safety observation helps prevent incidents and keeps our workplace safer for everyone. Your voice matters.\n\n**What type of safety concern would you like to report?**",
                "type": "safety_guide",
                "actions": [
                    {
                        "text": "⚠️ Unsafe Condition",
                        "action": "navigate",
                        "url": "/safety-concerns/new?type=condition"
                    },
                    {
                        "text": "👤 Unsafe Behavior",
                        "action": "navigate",
                        "url": "/safety-concerns/new?type=behavior"
                    },
                    {
                        "text": "💡 Safety Suggestion",
                        "action": "navigate",
                        "url": "/safety-concerns/new?type=suggestion"
                    },
                    {
                        "text": "🎯 Safety Recognition",
                        "action": "navigate",
                        "url": "/safety-concerns/new?type=recognition"
                    },
                    {
                        "text": "📞 Anonymous Report",
                        "action": "navigate",
                        "url": "/safety-concerns/new?anonymous=true"
                    }
                ],
                "quick_replies": [
                    "I observed something unsafe",
                    "I want to suggest an improvement",
                    "I want to report anonymously",
                    "Someone deserves recognition"
                ],
                "guidance": "All reports are taken seriously and investigated promptly. Anonymous reports are completely confidential."
            }
            
        elif intent == "risk_assessment":
            return {
                "message": "📊 **I'll help you conduct a risk assessment using our ERC (Event Risk Classification) matrix.**\n\nOur system evaluates both likelihood and severity across five key categories: People, Environment, Cost, Reputation, and Legal impact.\n\n**Would you like to:**",
                "type": "risk_guide",
                "actions": [
                    {
                        "text": "🎯 Start New Risk Assessment",
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
                        "action": "continue_conversation",
                        "message": "Explain how the ERC risk matrix works"
                    }
                ],
                "quick_replies": [
                    "Start a new assessment",
                    "Show me existing risks",
                    "How does the ERC matrix work?",
                    "What are the severity categories?"
                ],
                "risk_info": {
                    "likelihood_scale": "0 (Impossible) to 10 (Almost Certain)",
                    "severity_categories": ["People", "Environment", "Cost", "Reputation", "Legal"],
                    "risk_levels": "Very Low (0-19), Low (20-39), Medium (40-59), High (60-79), Critical (80-100)"
                }
            }
            
        elif intent == "capa_management":
            return {
                "message": "🔄 **I'll help you with Corrective and Preventive Actions (CAPA).**\n\nCAPAs ensure we learn from incidents and continuously improve our safety performance.\n\n• **Corrective Actions:** Fix existing problems\n• **Preventive Actions:** Prevent future issues\n\n**What would you like to do?**",
                "type": "capa_guide",
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
                        "text": "⏰ View Overdue CAPAs",
                        "action": "continue_conversation",
                        "message": "Show me overdue CAPAs"
                    }
                ],
                "quick_replies": [
                    "Create a corrective action",
                    "Create a preventive action", 
                    "Show me my CAPAs",
                    "What's overdue?"
                ]
            }
            
        elif intent == "sds_lookup":
            return {
                "message": "📄 **I'll help you find Safety Data Sheets in our searchable library.**\n\nOur SDS system includes AI-powered chat functionality - you can ask questions about specific chemicals once you find them!\n\n**What would you like to do?**",
                "type": "sds_guide",
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
                        "text": "💬 Chat with Existing SDS",
                        "action": "continue_conversation",
                        "message": "Find a specific chemical to chat with"
                    }
                ],
                "quick_replies": [
                    "Search for acetone",
                    "Search for ammonia",
                    "Upload a new SDS document",
                    "Show me all chemicals"
                ],
                "guidance": "Pro tip: Upload PDFs or use our chat feature to ask questions like 'What PPE is required?' or 'What are the fire hazards?'"
            }
            
        elif intent == "dashboard_overview":
            return self.get_dashboard_overview()
            
        elif intent == "help_request":
            return {
                "message": "🤖 **I'm your Smart EHS Assistant - here to make safety management easy!**\n\nI can help you with:\n\n🚨 **Safety Operations**\n• Report incidents and safety concerns\n• Conduct risk assessments\n• Manage corrective actions (CAPAs)\n\n📚 **Information & Resources**\n• Find safety data sheets\n• Search system data\n• Get guidance on EHS processes\n\n📊 **Monitoring & Analysis**\n• View dashboard overviews\n• Check urgent items\n• Track system status\n\n**Just tell me what you need in plain language!**",
                "type": "help_menu",
                "quick_replies": [
                    "Report a workplace incident",
                    "Submit a safety concern",
                    "Find a safety data sheet",
                    "What needs my attention?",
                    "Show me the dashboard"
                ]
            }
            
        else:  # general_inquiry
            return {
                "message": "🤖 **I'm here to help with your EHS needs!**\n\nI can assist you with:\n\n• **Reporting incidents** and safety concerns\n• **Risk assessments** and safety analysis  \n• **Finding information** like safety data sheets\n• **Managing CAPAs** and corrective actions\n• **System overviews** and urgent items\n\nWhat would you like to work on?",
                "type": "general_help",
                "quick_replies": [
                    "Report an incident",
                    "Safety concern",
                    "Risk assessment", 
                    "Find SDS",
                    "What's urgent?"
                ]
            }
    
    def get_dashboard_overview(self) -> Dict:
        """Get current system status and urgent items"""
        try:
            stats = self.load_system_stats()
            urgent = self.get_urgent_items()
            
            message = "📊 **EHS System Overview**\n\n"
            
            if urgent:
                message += "🚨 **Items Requiring Immediate Attention:**\n"
                for item in urgent[:3]:
                    emoji = "🔴" if item.get("priority") == "critical" else "🟡"
                    message += f"{emoji} {item['type']}: {item['description']}\n"
                message += "\n"
            
            message += f"📈 **Current Status:**\n"
            message += f"• Open Incidents: **{stats.get('open_incidents', 0)}**\n"
            message += f"• Overdue CAPAs: **{stats.get('overdue_capas', 0)}**\n" 
            message += f"• Safety Concerns: **{stats.get('safety_concerns', 0)}**\n"
            message += f"• High Risk Items: **{stats.get('high_risk', 0)}**\n\n"
            
            message += "What would you like to address first?"
            
            actions = [
                {
                    "text": "🚨 Address Urgent Items",
                    "action": "continue_conversation",
                    "message": "Help me with the most urgent items"
                },
                {
                    "text": "📝 Report New Incident", 
                    "action": "continue_conversation",
                    "message": "I need to report a workplace incident"
                },
                {
                    "text": "📊 Full Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ]
            
            return {
                "message": message,
                "type": "dashboard_overview", 
                "actions": actions,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "message": "📊 **EHS System Overview**\n\nI'm ready to help you with:\n\n• 🚨 **Report incidents** and safety concerns\n• 📋 **Manage CAPAs** and corrective actions\n• 📊 **Conduct risk assessments**\n• 📄 **Find safety data sheets**\n• 👥 **Manage contractors** and compliance\n\nWhat would you like to work on?",
                "type": "dashboard_fallback",
                "actions": [
                    {
                        "text": "📝 Report Incident",
                        "action": "continue_conversation", 
                        "message": "I need to report a workplace incident"
                    },
                    {
                        "text": "🛡️ Safety Concern",
                        "action": "continue_conversation",
                        "message": "I want to report a safety concern"
                    }
                ]
            }
    
    def handle_file_upload(self, message: str, file_info: Dict) -> Dict:
        """Handle file uploads intelligently based on file type"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can see you've uploaded a photo. This is perfect for:\n\n• **Incident evidence** - Photos help investigations\n• **Safety observations** - Visual proof of concerns\n• **Audit findings** - Document non-compliance\n\nWhat would you like to do with this image?",
                "type": "image_upload",
                "actions": [
                    {
                        "text": "🚨 Use for Incident Report",
                        "action": "navigate",
                        "url": f"/incidents/new?photo={file_info.get('path', '')}"
                    },
                    {
                        "text": "🛡️ Use for Safety Concern", 
                        "action": "navigate",
                        "url": f"/safety-concerns/new?photo={file_info.get('path', '')}"
                    }
                ],
                "quick_replies": [
                    "This shows an injury",
                    "This shows damage",
                    "This shows a hazard",
                    "This is for documentation"
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nPerfect! PDF documents are commonly used for:\n\n• **Safety Data Sheets** - Chemical safety information\n• **Incident documentation** - Supporting evidence\n• **Compliance records** - Regulatory documentation\n\nWhat type of document is this?",
                "type": "pdf_upload",
                "actions": [
                    {
                        "text": "📋 Add to SDS Library",
                        "action": "navigate",
                        "url": f"/sds/upload?file={file_info.get('path', '')}"
                    },
                    {
                        "text": "📎 Attach to Report",
                        "action": "continue_conversation",
                        "message": "I want to attach this to an incident or safety report"
                    }
                ],
                "quick_replies": [
                    "This is a safety data sheet",
                    "This is incident documentation", 
                    "This is a compliance document",
                    "This is training material"
                ]
            }
        else:
            return {
                "message": f"📎 **File received: {filename}**\n\nI've received your document. How would you like to use it in our EHS system?",
                "type": "general_upload",
                "actions": [
                    {
                        "text": "📝 Attach to Report",
                        "action": "continue_conversation", 
                        "message": "Attach this file to an incident or safety report"
                    },
                    {
                        "text": "📚 Use for Documentation",
                        "action": "continue_conversation",
                        "message": "This is supporting documentation"
                    }
                ],
                "quick_replies": [
                    "Use for incident report",
                    "Use for safety documentation",
                    "Add to compliance records"
                ]
            }
    
    def is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        emergency_keywords = [
            "emergency", "911", "fire", "bleeding", "unconscious", "heart attack",
            "severe injury", "immediate danger", "life threatening", "call ambulance"
        ]
        return any(keyword in message for keyword in emergency_keywords)
    
    def handle_emergency(self) -> Dict:
        """Emergency response"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR LIFE-THREATENING EMERGENCIES:**\n📞 **CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568  \n• EHS Hotline: (555) 123-4569\n\n**After ensuring everyone's safety, I can help you document this incident in our system.**",
            "type": "emergency",
            "actions": [
                {
                    "text": "📝 Report Emergency Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency"
                }
            ]
        }
    
    def load_system_stats(self) -> Dict:
        """Load actual system statistics"""
        stats = {}
        
        try:
            # Load incidents
            incidents_file = Path("data/incidents.json")
            if incidents_file.exists():
                incidents = json.loads(incidents_file.read_text())
                stats["open_incidents"] = len([i for i in incidents.values() if i.get("status") != "complete"])
            
            # Load safety concerns  
            concerns_file = Path("data/safety_concerns.json")
            if concerns_file.exists():
                concerns = json.loads(concerns_file.read_text())
                stats["safety_concerns"] = len([c for c in concerns.values() if c.get("status") in ["reported", "in_progress"]])
            
            # Load CAPAs
            capa_file = Path("data/capa.json")
            if capa_file.exists():
                capas = json.loads(capa_file.read_text())
                today = datetime.now().date()
                overdue = 0
                for capa in capas.values():
                    if capa.get("status") in ["open", "in_progress"]:
                        try:
                            due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                            if due_date < today:
                                overdue += 1
                        except:
                            pass
                stats["overdue_capas"] = overdue
            
            # Load risk assessments
            risk_file = Path("data/risk_assessments.json") 
            if risk_file.exists():
                risks = json.loads(risk_file.read_text())
                stats["high_risk"] = len([r for r in risks.values() if r.get("risk_level") in ["High", "Critical"]])
                
        except Exception as e:
            print(f"Error loading stats: {e}")
            
        return stats
    
    def get_urgent_items(self) -> List[Dict]:
        """Get urgent items needing attention"""
        urgent = []
        
        try:
            # Check overdue CAPAs
            capa_file = Path("data/capa.json")
            if capa_file.exists():
                capas = json.loads(capa_file.read_text())
                today = datetime.now().date()
                
                for capa in capas.values():
                    if capa.get("status") in ["open", "in_progress"]:
                        try:
                            due_date = datetime.fromisoformat(capa.get("due_date", "")).date()
                            if due_date < today:
                                days_overdue = (today - due_date).days
                                urgent.append({
                                    "type": "Overdue CAPA",
                                    "description": capa.get("title", "Unknown CAPA")[:50],
                                    "days_overdue": days_overdue,
                                    "priority": "critical" if days_overdue > 14 else "high"
                                })
                        except:
                            pass
        except:
            pass
            
        return sorted(urgent, key=lambda x: x.get("days_overdue", 0), reverse=True)
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary"""
        return {
            "message_count": len(self.conversation_history),
            "last_intent": self.conversation_history[-1].get("intent") if self.conversation_history else None,
            "timestamp": datetime.now().isoformat()
        }
