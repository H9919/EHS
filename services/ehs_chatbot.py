# services/ehs_chatbot.py - Enhanced AI Chatbot with Action Capabilities
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class EHSChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}
        self.active_workflows = {}  # Track ongoing form workflows
        
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Enhanced message processing with action capabilities"""
        message = user_message.lower().strip()
        
        # Check for emergency first
        if self.is_emergency(message):
            return self.handle_emergency()
        
        # Check if user is in the middle of a workflow
        if user_id in self.active_workflows:
            return self.handle_workflow_step(user_message, user_id)
        
        # Detect intent and capability
        intent, action_type = self.detect_intent_and_action(message)
        
        # Generate response based on intent and action capability
        response = self.generate_enhanced_response(intent, action_type, user_message, user_id, context)
        
        # Update conversation history
        self.conversation_history.append({
            "user_message": user_message,
            "bot_response": response,
            "intent": intent,
            "action_type": action_type,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        })
        
        return response
    
    def detect_intent_and_action(self, message: str) -> Tuple[str, str]:
        """Detect both intent and desired action type"""
        
        # Action-oriented patterns
        create_patterns = [
            r"(create|make|generate|start|begin|new)\s+(incident|capa|assessment|audit)",
            r"(report|file|submit)\s+(incident|concern|observation)",
            r"(fill out|complete)\s+(form|report)",
            r"help me (create|make|start|report)",
            r"I need to (report|create|make|start|file)"
        ]
        
        view_patterns = [
            r"(show|display|view|see|find|get|list)\s+(incidents|capas|concerns|audits|sds)",
            r"what.*pending|overdue|outstanding",
            r"(check|review)\s+(status|progress)",
            r"(dashboard|summary|overview)"
        ]
        
        help_patterns = [
            r"(help|guide|assist|explain|how)",
            r"what (is|are|can|should)",
            r"(understand|learn about)",
            r"(show me|tell me about)"
        ]
        
        # Intent detection
        intent = "general_inquiry"
        action_type = "conversation"
        
        # Check for specific module intents with action types
        if re.search(r"incident", message):
            intent = "incident_management"
            if any(re.search(pattern, message) for pattern in create_patterns):
                action_type = "create_form"
            elif any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "view_data"
        
        elif re.search(r"safety.*concern|observation|near.*miss", message):
            intent = "safety_concern"
            if any(re.search(pattern, message) for pattern in create_patterns):
                action_type = "create_form"
            elif any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "view_data"
        
        elif re.search(r"risk.*assessment|risk.*matrix|erc", message):
            intent = "risk_assessment"
            if any(re.search(pattern, message) for pattern in create_patterns):
                action_type = "create_form"
            elif any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "view_data"
        
        elif re.search(r"capa|corrective|preventive", message):
            intent = "capa_management"
            if any(re.search(pattern, message) for pattern in create_patterns):
                action_type = "create_form"
            elif any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "view_data"
        
        elif re.search(r"audit|inspection|checklist", message):
            intent = "audit_inspection"
            if any(re.search(pattern, message) for pattern in create_patterns):
                action_type = "create_form"
            elif any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "view_data"
        
        elif re.search(r"sds|safety.*data.*sheet|chemical", message):
            intent = "sds_lookup"
            if any(re.search(pattern, message) for pattern in view_patterns):
                action_type = "search_data"
        
        elif re.search(r"dashboard|overview|status|summary|what.*urgent|priority", message):
            intent = "dashboard_overview"
            action_type = "view_data"
        
        elif any(re.search(pattern, message) for pattern in help_patterns):
            intent = "help_guidance"
            action_type = "conversation"
        
        return intent, action_type
    
    def generate_enhanced_response(self, intent: str, action_type: str, message: str, user_id: str, context: Dict = None) -> Dict:
        """Generate responses with actual action capabilities"""
        
        if intent == "incident_management":
            if action_type == "create_form":
                return self.create_incident_form(user_id)
            elif action_type == "view_data":
                return self.show_incident_data()
            else:
                return self.get_incident_help()
        
        elif intent == "safety_concern":
            if action_type == "create_form":
                return self.create_safety_concern_form(user_id)
            elif action_type == "view_data":
                return self.show_safety_concern_data()
            else:
                return self.get_safety_concern_help()
        
        elif intent == "risk_assessment":
            if action_type == "create_form":
                return self.create_risk_assessment_form(user_id)
            elif action_type == "view_data":
                return self.show_risk_data()
            else:
                return self.get_risk_help()
        
        elif intent == "capa_management":
            if action_type == "create_form":
                return self.create_capa_form(user_id)
            elif action_type == "view_data":
                return self.show_capa_data()
            else:
                return self.get_capa_help()
        
        elif intent == "dashboard_overview":
            return self.show_dashboard_overview()
        
        elif intent == "sds_lookup":
            return self.handle_sds_search(message)
        
        else:
            return self.get_general_help()
    
    def create_incident_form(self, user_id: str) -> Dict:
        """Create an interactive incident report form"""
        
        # Start workflow
        self.active_workflows[user_id] = {
            "type": "incident_report",
            "step": 1,
            "data": {},
            "started": datetime.now().isoformat()
        }
        
        return {
            "message": "I'll help you report an incident step by step. Let's start with some basic information:",
            "type": "form_workflow",
            "form_widget": {
                "title": "Incident Report - Basic Information",
                "type": "incident",
                "fields": [
                    {
                        "type": "row",
                        "fields": [
                            {
                                "type": "select",
                                "name": "incident_type",
                                "label": "Incident Type",
                                "required": True,
                                "options": [
                                    {"value": "injury", "label": "Injury"},
                                    {"value": "near_miss", "label": "Near Miss"},
                                    {"value": "property_damage", "label": "Property Damage"},
                                    {"value": "environmental", "label": "Environmental"},
                                    {"value": "security", "label": "Security"},
                                    {"value": "vehicle", "label": "Vehicle"},
                                    {"value": "other", "label": "Other"}
                                ]
                            },
                            {
                                "type": "date",
                                "name": "incident_date",
                                "label": "Incident Date",
                                "required": True
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "name": "location",
                        "label": "Location",
                        "required": True,
                        "placeholder": "Where did this incident occur?"
                    },
                    {
                        "type": "textarea",
                        "name": "description",
                        "label": "Description",
                        "required": True,
                        "rows": 4,
                        "placeholder": "Please describe what happened in detail..."
                    }
                ]
            },
            "actions": [
                {
                    "text": "Skip Form - Just Tell Me",
                    "action": "continue_conversation",
                    "message": "I'd prefer to just tell you about the incident in conversation"
                }
            ]
        }
    
    def create_safety_concern_form(self, user_id: str) -> Dict:
        """Create a safety concern form"""
        
        self.active_workflows[user_id] = {
            "type": "safety_concern",
            "step": 1,
            "data": {},
            "started": datetime.now().isoformat()
        }
        
        return {
            "message": "Thank you for speaking up about a safety concern! Every observation helps keep our workplace safe. Let me help you submit this:",
            "type": "form_workflow",
            "form_widget": {
                "title": "Safety Concern Report",
                "type": "safety_concern",
                "fields": [
                    {
                        "type": "row",
                        "fields": [
                            {
                                "type": "select",
                                "name": "concern_type",
                                "label": "Type of Concern",
                                "required": True,
                                "options": [
                                    {"value": "unsafe_condition", "label": "Unsafe Condition"},
                                    {"value": "unsafe_behavior", "label": "Unsafe Behavior"},
                                    {"value": "near_miss", "label": "Near Miss"},
                                    {"value": "suggestion", "label": "Safety Suggestion"},
                                    {"value": "recognition", "label": "Safety Recognition"}
                                ]
                            },
                            {
                                "type": "select",
                                "name": "priority",
                                "label": "Priority Level",
                                "required": True,
                                "options": [
                                    {"value": "low", "label": "Low - Minor concern"},
                                    {"value": "medium", "label": "Medium - Moderate concern"},
                                    {"value": "high", "label": "High - Serious concern"},
                                    {"value": "critical", "label": "Critical - Immediate danger"}
                                ]
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "name": "location",
                        "label": "Location",
                        "required": True,
                        "placeholder": "Where did you observe this?"
                    },
                    {
                        "type": "textarea",
                        "name": "description",
                        "label": "Description",
                        "required": True,
                        "rows": 4,
                        "placeholder": "Please describe what you observed..."
                    },
                    {
                        "type": "textarea",
                        "name": "immediate_action",
                        "label": "Immediate Action Taken",
                        "required": False,
                        "rows": 2,
                        "placeholder": "What immediate steps were taken (if any)?"
                    }
                ]
            }
        }
    
    def create_risk_assessment_form(self, user_id: str) -> Dict:
        """Create a risk assessment form"""
        
        self.active_workflows[user_id] = {
            "type": "risk_assessment",
            "step": 1,
            "data": {},
            "started": datetime.now().isoformat()
        }
        
        return {
            "message": "I'll guide you through our Event Risk Classification (ERC) process. This evaluates likelihood and severity across five key areas:",
            "type": "form_workflow",
            "form_widget": {
                "title": "Risk Assessment - ERC Matrix",
                "type": "risk_assessment",
                "fields": [
                    {
                        "type": "text",
                        "name": "risk_title",
                        "label": "Risk Title",
                        "required": True,
                        "placeholder": "Brief description of the risk scenario"
                    },
                    {
                        "type": "textarea",
                        "name": "risk_description",
                        "label": "Risk Description",
                        "required": True,
                        "rows": 3,
                        "placeholder": "Detailed description of the potential risk..."
                    },
                    {
                        "type": "select",
                        "name": "likelihood",
                        "label": "Likelihood (0-10)",
                        "required": True,
                        "options": [
                            {"value": "0", "label": "0 - Impossible"},
                            {"value": "2", "label": "2 - Rare (once in 10+ years)"},
                            {"value": "4", "label": "4 - Unlikely (once every 5-10 years)"},
                            {"value": "6", "label": "6 - Possible (once every 1-5 years)"},
                            {"value": "8", "label": "8 - Likely (multiple times per year)"},
                            {"value": "10", "label": "10 - Almost Certain (monthly or more)"}
                        ]
                    }
                ]
            },
            "actions": [
                {
                    "text": "Learn About ERC Matrix",
                    "action": "continue_conversation",
                    "message": "Can you explain how the ERC matrix works?"
                }
            ]
        }
    
    def create_capa_form(self, user_id: str) -> Dict:
        """Create a CAPA form"""
        
        self.active_workflows[user_id] = {
            "type": "capa",
            "step": 1,
            "data": {},
            "started": datetime.now().isoformat()
        }
        
        return {
            "message": "I'll help you create a Corrective and Preventive Action (CAPA). Let's start with the basic information:",
            "type": "form_workflow",
            "form_widget": {
                "title": "Create CAPA",
                "type": "capa",
                "fields": [
                    {
                        "type": "text",
                        "name": "title",
                        "label": "CAPA Title",
                        "required": True,
                        "placeholder": "Brief description of the corrective/preventive action"
                    },
                    {
                        "type": "row",
                        "fields": [
                            {
                                "type": "select",
                                "name": "type",
                                "label": "CAPA Type",
                                "required": True,
                                "options": [
                                    {"value": "corrective", "label": "Corrective Action (fix current problem)"},
                                    {"value": "preventive", "label": "Preventive Action (prevent future problems)"}
                                ]
                            },
                            {
                                "type": "select",
                                "name": "priority",
                                "label": "Priority",
                                "required": True,
                                "options": [
                                    {"value": "low", "label": "Low"},
                                    {"value": "medium", "label": "Medium"},
                                    {"value": "high", "label": "High"},
                                    {"value": "critical", "label": "Critical"}
                                ]
                            }
                        ]
                    },
                    {
                        "type": "textarea",
                        "name": "description",
                        "label": "Description",
                        "required": True,
                        "rows": 3,
                        "placeholder": "Detailed description of the problem and proposed action"
                    },
                    {
                        "type": "row",
                        "fields": [
                            {
                                "type": "text",
                                "name": "assignee",
                                "label": "Assignee",
                                "required": True,
                                "placeholder": "Person responsible for implementation"
                            },
                            {
                                "type": "date",
                                "name": "due_date",
                                "label": "Due Date",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        }
    
    def show_dashboard_overview(self) -> Dict:
        """Show system overview and urgent items"""
        
        try:
            # Load actual data
            urgent_items = self.get_urgent_items()
            stats = self.get_system_stats()
            
            message = f"**System Overview** 📊\n\n"
            
            if urgent_items:
                message += "**⚠️ Items Requiring Attention:**\n"
                for item in urgent_items[:5]:
                    message += f"• {item['type']}: {item['description']} ({item['days_overdue']} days overdue)\n"
                message += "\n"
            
            message += f"""**📈 Current Statistics:**
• Open Incidents: {stats.get('incidents', {}).get('open', 0)}
• Overdue CAPAs: {stats.get('capas', {}).get('overdue', 0)}
• Safety Concerns: {stats.get('safety_concerns', {}).get('open', 0)}
• High Risk Items: {stats.get('risk_assessments', {}).get('high_risk', 0)}

What would you like to work on?"""
            
            actions = [
                {
                    "text": "Address Urgent Items",
                    "action": "continue_conversation",
                    "message": "Help me address the most urgent items first"
                },
                {
                    "text": "Report New Incident",
                    "action": "continue_conversation",
                    "message": "I need to report a new incident"
                },
                {
                    "text": "View Full Dashboard",
                    "action": "navigate",
                    "url": "/dashboard/analytics"
                }
            ]
            
            return {
                "message": message,
                "type": "dashboard_overview",
                "actions": actions
            }
            
        except Exception as e:
            return {
                "message": "Here's what I can help you with today:\n\n• Report incidents and safety concerns\n• Create and manage CAPAs\n• Conduct risk assessments\n• Find safety data sheets\n• Review audit findings\n\nWhat would you like to work on?",
                "type": "fallback_overview"
            }
    
    def handle_workflow_step(self, message: str, user_id: str) -> Dict:
        """Handle ongoing form workflow steps"""
        
        workflow = self.active_workflows.get(user_id)
        if not workflow:
            return self.get_general_help()
        
        # Parse form data from message
        try:
            # Assuming message contains JSON form data
            if message.startswith("Here's the completed form data:"):
                form_data = json.loads(message.split(":", 1)[1].strip())
                return self.complete_workflow(user_id, form_data)
        except:
            pass
        
        # Handle conversational workflow
        if "cancel" in message.lower():
            del self.active_workflows[user_id]
            return {
                "message": "I've cancelled the form. What else can I help you with?",
                "type": "workflow_cancelled"
            }
        
        # Continue with conversational form filling
        return self.continue_conversational_workflow(user_id, message)
    
    def complete_workflow(self, user_id: str, form_data: Dict) -> Dict:
        """Complete a workflow by submitting the form data"""
        
        workflow = self.active_workflows.get(user_id)
        if not workflow:
            return {"message": "No active workflow found.", "type": "error"}
        
        workflow_type = workflow["type"]
        
        try:
            if workflow_type == "incident_report":
                result = self.submit_incident(form_data)
            elif workflow_type == "safety_concern":
                result = self.submit_safety_concern(form_data)
            elif workflow_type == "risk_assessment":
                result = self.submit_risk_assessment(form_data)
            elif workflow_type == "capa":
                result = self.submit_capa(form_data)
            else:
                result = {"success": False, "error": "Unknown workflow type"}
            
            # Clean up workflow
            del self.active_workflows[user_id]
            
            if result.get("success"):
                return {
                    "message": f"✅ {workflow_type.replace('_', ' ').title()} submitted successfully!\n\n**ID:** {result['id']}\n\nWhat else can I help you with?",
                    "type": "workflow_completed",
                    "actions": [
                        {
                            "text": f"View {workflow_type.replace('_', ' ').title()}",
                            "action": "navigate",
                            "url": result["url"]
                        },
                        {
                            "text": "Create Another",
                            "action": "continue_conversation",
                            "message": f"I want to create another {workflow_type.replace('_', ' ')}"
                        }
                    ]
                }
            else:
                return {
                    "message": f"❌ There was an error submitting the {workflow_type}: {result.get('error', 'Unknown error')}",
                    "type": "workflow_error"
                }
                
        except Exception as e:
            del self.active_workflows[user_id]
            return {
                "message": f"❌ There was an error processing your {workflow_type}: {str(e)}",
                "type": "workflow_error"
            }
    
    def submit_incident(self, data: Dict) -> Dict:
        """Actually submit an incident to the system"""
        try:
            # Create incident record
            incident_data = {
                "id": str(int(time.time() * 1000)),
                "type": data.get("incident_type", "other"),
                "created_ts": time.time(),
                "status": "draft",
                "answers": {
                    "people": data.get("description", ""),
                    "environment": "",
                    "cost": "",
                    "legal": "",
                    "reputation": ""
                },
                "location": data.get("location", ""),
                "incident_date": data.get("incident_date", ""),
                "created_via": "ai_assistant"
            }
            
            # Save to incidents file
            incidents_file = Path("data/incidents.json")
            if incidents_file.exists():
                incidents = json.loads(incidents_file.read_text())
            else:
                incidents = {}
            
            incidents[incident_data["id"]] = incident_data
            
            incidents_file.parent.mkdir(exist_ok=True)
            incidents_file.write_text(json.dumps(incidents, indent=2))
            
            return {
                "success": True,
                "id": incident_data["id"],
                "url": f"/incidents/{incident_data['id']}/edit"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_safety_concern(self, data: Dict) -> Dict:
        """Submit a safety concern"""
        try:
            concern_data = {
                "id": str(int(time.time() * 1000)),
                "type": data.get("concern_type", "unsafe_condition"),
                "title": f"{data.get('concern_type', 'Safety')} concern at {data.get('location', 'Unknown location')}",
                "description": data.get("description", ""),
                "location": data.get("location", ""),
                "immediate_action": data.get("immediate_action", ""),
                "priority": data.get("priority", "medium"),
                "created_date": time.time(),
                "status": "reported",
                "anonymous": False,
                "reporter": "AI Assistant User",
                "created_via": "ai_assistant"
            }
            
            # Save to safety concerns file
            concerns_file = Path("data/safety_concerns.json")
            if concerns_file.exists():
                concerns = json.loads(concerns_file.read_text())
            else:
                concerns = {}
            
            concerns[concern_data["id"]] = concern_data
            
            concerns_file.parent.mkdir(exist_ok=True)
            concerns_file.write_text(json.dumps(concerns, indent=2))
            
            return {
                "success": True,
                "id": concern_data["id"],
                "url": f"/safety-concerns/{concern_data['id']}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_capa(self, data: Dict) -> Dict:
        """Submit a CAPA"""
        try:
            from services.capa_manager import CAPAManager
            capa_manager = CAPAManager()
            
            capa_data = {
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "type": data.get("type", "corrective"),
                "priority": data.get("priority", "medium"),
                "assignee": data.get("assignee", ""),
                "due_date": data.get("due_date", ""),
                "created_by": "AI Assistant User",
                "source": "ai_assistant"
            }
            
            capa_id = capa_manager.create_capa(capa_data)
            
            return {
                "success": True,
                "id": capa_id,
                "url": f"/capa/{capa_id}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_emergency(self, message: str) -> bool:
        """Check if message indicates emergency"""
        emergency_keywords = [
            "emergency", "fire", "injury", "hurt", "bleeding", "unconscious",
            "911", "help", "urgent", "immediate", "danger", "accident"
        ]
        return any(keyword in message for keyword in emergency_keywords)
    
    def handle_emergency(self) -> Dict:
        """Handle emergency situations"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**If this is a life-threatening emergency, call 911 immediately.**\n\nFor other emergencies:\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569\n\nAfter ensuring safety, I can help you report this incident through our system.",
            "type": "emergency",
            "priority": "critical",
            "actions": [
                {
                    "text": "Report Emergency Incident",
                    "action": "continue_conversation",
                    "message": "I need to report this emergency incident"
                },
                {
                    "text": "Get Emergency Procedures",
                    "action": "navigate",
                    "url": "/emergency-procedures"
                }
            ]
        }
    
    def get_urgent_items(self) -> List[Dict]:
        """Get urgent items requiring attention"""
        urgent_items = []
        
        try:
            # Check overdue CAPAs
            from services.capa_manager import CAPAManager
            capa_manager = CAPAManager()
            overdue_capas = capa_manager.get_overdue_capas()
            
            for capa in overdue_capas[:3]:  # Top 3
                urgent_items.append({
                    "type": "Overdue CAPA",
                    "description": capa.get("title", "Unknown CAPA"),
                    "days_overdue": capa.get("days_overdue", 0),
                    "url": f"/capa/{capa['id']}"
                })
        except:
            pass
        
        try:
            # Check unresolved safety concerns
            concerns_file = Path("data/safety_concerns.json")
            if concerns_file.exists():
                concerns = json.loads(concerns_file.read_text())
                
                for concern in concerns.values():
                    if concern.get("status") == "reported":
                        created_date = datetime.fromtimestamp(concern.get("created_date", 0))
                        days_open = (datetime.now() - created_date).days
                        
                        if days_open > 1:  # Over 1 day without response
                            urgent_items.append({
                                "type": "Unresolved Safety Concern",
                                "description": concern.get("title", "Safety concern"),
                                "days_overdue": days_open,
                                "url": f"/safety-concerns/{concern['id']}"
                            })
        except:
            pass
        
        return sorted(urgent_items, key=lambda x: x["days_overdue"], reverse=True)
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        try:
            from services.dashboard_stats import get_dashboard_statistics
            return get_dashboard_statistics()
        except:
            return {}
    
    def show_incident_data(self) -> Dict:
        """Show incident data"""
        try:
            incidents_file = Path("data/incidents.json")
            if incidents_file.exists():
                incidents = json.loads(incidents_file.read_text())
                
                open_incidents = [i for i in incidents.values() if i.get("status") != "complete"]
                recent_incidents = sorted(incidents.values(), key=lambda x: x.get("created_ts", 0), reverse=True)[:5]
                
                message = f"**📋 Incident Overview**\n\n**Open Incidents:** {len(open_incidents)}\n**Total Incidents:** {len(incidents)}\n\n"
                
                if recent_incidents:
                    message += "**Recent Incidents:**\n"
                    for incident in recent_incidents:
                        status = incident.get("status", "unknown")
                        incident_type = incident.get("type", "unknown")
                        message += f"• {incident_type.title()} - {status.title()}\n"
                
                return {
                    "message": message,
                    "type": "data_display",
                    "actions": [
                        {
                            "text": "View All Incidents",
                            "action": "navigate",
                            "url": "/incidents"
                        },
                        {
                            "text": "Report New Incident",
                            "action": "continue_conversation",
                            "message": "I need to report a new incident"
                        }
                    ]
                }
            else:
                return {
                    "message": "No incidents found in the system yet. Would you like to report one?",
                    "type": "no_data",
                    "actions": [
                        {
                            "text": "Report First Incident",
                            "action": "continue_conversation",
                            "message": "I need to report an incident"
                        }
                    ]
                }
        except Exception as e:
            return {
                "message": "I'm having trouble accessing incident data right now. You can view incidents directly using the sidebar navigation.",
                "type": "data_error"
            }
    
    def show_capa_data(self) -> Dict:
        """Show CAPA data"""
        try:
            from services.capa_manager import CAPAManager
            capa_manager = CAPAManager()
            
            stats = capa_manager.get_capa_statistics()
            overdue = capa_manager.get_overdue_capas()
            
            message = f"**🔄 CAPA Overview**\n\n"
            message += f"**Total CAPAs:** {stats['total']}\n"
            message += f"**Open:** {stats['open']}\n"
            message += f"**In Progress:** {stats['in_progress']}\n"
            message += f"**Completed:** {stats['completed']}\n"
            message += f"**⚠️ Overdue:** {stats['overdue']}\n\n"
            
            if overdue:
                message += "**Most Overdue CAPAs:**\n"
                for capa in overdue[:3]:
                    message += f"• {capa.get('title', 'Unknown')[:50]} ({capa.get('days_overdue', 0)} days overdue)\n"
            
            return {
                "message": message,
                "type": "data_display",
                "actions": [
                    {
                        "text": "View CAPA Dashboard",
                        "action": "navigate",
                        "url": "/capa/dashboard"
                    },
                    {
                        "text": "Create New CAPA",
                        "action": "continue_conversation",
                        "message": "I need to create a new CAPA"
                    }
                ] + ([{
                    "text": "Address Overdue CAPAs",
                    "action": "navigate",
                    "url": "/capa"
                }] if overdue else [])
            }
            
        except Exception as e:
            return {
                "message": "I'm having trouble accessing CAPA data. You can view CAPAs using the sidebar navigation.",
                "type": "data_error"
            }
    
    def handle_sds_search(self, message: str) -> Dict:
        """Handle SDS search requests"""
        # Extract chemical name from message
        chemical_keywords = ["acetone", "ammonia", "bleach", "alcohol", "acid", "sodium", "chlorine", "hydrogen"]
        found_chemical = None
        
        for keyword in chemical_keywords:
            if keyword in message.lower():
                found_chemical = keyword
                break
        
        if found_chemical:
            return {
                "message": f"I'll help you find the SDS for **{found_chemical}**. Let me search our library...",
                "type": "sds_search",
                "actions": [
                    {
                        "text": "Search SDS Library",
                        "action": "navigate",
                        "url": f"/sds?search={found_chemical}"
                    },
                    {
                        "text": "Upload New SDS",
                        "action": "navigate",
                        "url": "/sds/upload"
                    }
                ],
                "quick_replies": [
                    "Show me all available SDS",
                    "How do I upload a new SDS?",
                    "What PPE is required for this chemical?"
                ]
            }
        else:
            return {
                "message": "I can help you find Safety Data Sheets in our library. What chemical are you looking for?",
                "type": "sds_help",
                "actions": [
                    {
                        "text": "Browse SDS Library",
                        "action": "navigate",
                        "url": "/sds"
                    },
                    {
                        "text": "Upload SDS",
                        "action": "navigate",
                        "url": "/sds/upload"
                    }
                ],
                "quick_replies": [
                    "Search for acetone SDS",
                    "Find ammonia safety data sheet",
                    "Show me all chemicals"
                ]
            }
    
    def get_incident_help(self) -> Dict:
        """Get incident management help"""
        return {
            "message": "**🚨 Incident Management Help**\n\nI can help you with:\n• **Report new incidents** - I'll guide you through our form\n• **View existing incidents** - See status and details\n• **Understand incident types** - Learn what's reportable\n• **Check validation requirements** - What information is needed\n\nWhat would you like to do?",
            "type": "help",
            "actions": [
                {
                    "text": "Report New Incident",
                    "action": "continue_conversation",
                    "message": "I need to report an incident"
                },
                {
                    "text": "View All Incidents",
                    "action": "navigate",
                    "url": "/incidents"
                }
            ],
            "quick_replies": [
                "What types of incidents should I report?",
                "How quickly must I report an incident?",
                "Can I report anonymously?"
            ]
        }
    
    def get_general_help(self) -> Dict:
        """Get general help"""
        return {
            "message": "**👋 I'm your Smart EHS Assistant!**\n\nI can help you with:\n\n🚨 **Report & Manage**\n• Incidents and accidents\n• Safety concerns and observations\n• Risk assessments\n\n📋 **Track & Monitor**\n• CAPAs (Corrective & Preventive Actions)\n• Audit findings and inspections\n• Safety data sheets (SDS)\n\n📊 **Analyze & Review**\n• Dashboard overviews\n• Urgent items and overdue tasks\n• System status and metrics\n\nJust tell me what you need help with in plain language!",
            "type": "general_help",
            "quick_replies": [
                "What needs my attention today?",
                "Report a safety incident",
                "Create a corrective action",
                "Find a safety data sheet",
                "Show me system overview"
            ]
        }
    
    def continue_conversational_workflow(self, user_id: str, message: str) -> Dict:
        """Continue a workflow conversationally instead of using forms"""
        workflow = self.active_workflows[user_id]
        workflow_type = workflow["type"]
        
        # Simple conversational collection
        if workflow_type == "incident_report":
            return {
                "message": "I understand you'd prefer to tell me about the incident conversationally. Please describe what happened, and I'll help organize the information for the report.",
                "type": "conversational_workflow",
                "quick_replies": [
                    "It was a slip and fall",
                    "Someone got injured",
                    "There was equipment damage",
                    "It was a near miss"
                ]
            }
        
        # For now, fallback to encouraging form use
        return {
            "message": "I'm still learning how to handle complex forms conversationally. For now, the form method ensures we capture all required information correctly. Would you like to try the form, or should I direct you to the appropriate page?",
            "type": "workflow_fallback",
            "actions": [
                {
                    "text": "Use the Form",
                    "action": "continue_conversation",
                    "message": f"Ok, let's use the form for the {workflow_type}"
                },
                {
                    "text": "Go to Page",
                    "action": "navigate",
                    "url": f"/{workflow_type.replace('_', '-')}/new"
                }
            ]
        }
