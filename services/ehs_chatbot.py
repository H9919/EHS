# services/ehs_chatbot.py - Enhanced with file upload support and better responses
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class EHSChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}
        self.active_workflows = {}  # Track ongoing form workflows
        
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Enhanced message processing with file upload and action capabilities"""
        message = user_message.lower().strip()
        context = context or {}
        
        # Check for uploaded file
        uploaded_file = context.get("uploaded_file")
        
        # Check for emergency first
        if self.is_emergency(message):
            return self.handle_emergency()
        
        # Handle file uploads with contextual responses
        if uploaded_file:
            return self.handle_file_upload(user_message, uploaded_file, user_id, context)
        
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
            "user_id": user_id,
            "had_file": bool(uploaded_file)
        })
        
        return response

    def handle_file_upload(self, user_message: str, uploaded_file: Dict, user_id: str, context: Dict) -> Dict:
        """Handle file uploads with appropriate responses"""
        filename = uploaded_file.get("filename", "")
        file_type = uploaded_file.get("type", "")
        file_path = uploaded_file.get("path", "")
        
        # Determine file purpose based on type and message context
        if file_type.startswith('image/'):
            return self.handle_image_upload(user_message, uploaded_file, user_id)
        elif file_type == 'application/pdf':
            return self.handle_pdf_upload(user_message, uploaded_file, user_id)
        else:
            return self.handle_document_upload(user_message, uploaded_file, user_id)

    def handle_image_upload(self, message: str, file_info: Dict, user_id: str) -> Dict:
        """Handle image uploads - typically for incident reports or safety concerns"""
        filename = file_info.get("filename", "")
        
        # Check if it's likely for an incident report
        incident_keywords = ["incident", "accident", "injury", "damage", "spill", "hazard"]
        is_incident = any(keyword in message.lower() for keyword in incident_keywords)
        
        if is_incident:
            return {
                "message": f"📸 **Image Received: {filename}**\n\nI can see you've uploaded a photo, likely related to an incident or safety concern. This visual evidence will be very helpful for the investigation.\n\nLet me help you create a proper incident report with this photo attached.",
                "type": "incident_photo",
                "actions": [
                    {
                        "text": "Create Incident Report",
                        "action": "navigate",
                        "url": f"/incidents/new?photo={file_info.get('path', '')}",
                        "style": "danger"
                    },
                    {
                        "text": "Report Safety Concern",
                        "action": "navigate", 
                        "url": f"/safety-concerns/new?photo={file_info.get('path', '')}",
                        "style": "warning"
                    }
                ],
                "quick_replies": [
                    "This is for an injury incident",
                    "This is environmental damage", 
                    "This is a safety hazard",
                    "This is property damage"
                ],
                "guidance": "Photos are crucial evidence for incident investigations. I'll make sure this image is properly attached to your report and preserved for the investigation team."
            }
        else:
            return {
                "message": f"📸 **Image Received: {filename}**\n\nI've received your image. How would you like me to help you with this?",
                "type": "general_photo",
                "actions": [
                    {
                        "text": "Report Incident with Photo",
                        "action": "continue_conversation",
                        "message": "I want to report an incident and this photo is evidence"
                    },
                    {
                        "text": "Submit Safety Observation",
                        "action": "continue_conversation",
                        "message": "I want to submit a safety concern with this photo"
                    },
                    {
                        "text": "Document Audit Finding",
                        "action": "continue_conversation",
                        "message": "This photo shows an audit finding or non-compliance"
                    }
                ],
                "quick_replies": [
                    "This shows a safety hazard",
                    "This is damage that occurred",
                    "This is for documentation",
                    "Help me understand what to do"
                ]
            }

    def handle_pdf_upload(self, message: str, file_info: Dict, user_id: str) -> Dict:
        """Handle PDF uploads - typically SDS or documents"""
        filename = file_info.get("filename", "")
        
        # Check if it's likely an SDS
        sds_keywords = ["sds", "safety data sheet", "material", "chemical", "msds"]
        is_sds = any(keyword in message.lower() for keyword in sds_keywords) or \
                 any(keyword in filename.lower() for keyword in sds_keywords)
        
        if is_sds:
            return {
                "message": f"📄 **SDS Document Received: {filename}**\n\nI can see you've uploaded what appears to be a Safety Data Sheet. Let me help you add this to our SDS library where it will be:\n\n• 🔍 **Searchable** by chemical name\n• 💬 **Chattable** - you can ask questions about it\n• 📱 **QR coded** for quick mobile access\n• 🏷️ **Properly indexed** for easy retrieval",
                "type": "sds_upload",
                "actions": [
                    {
                        "text": "Add to SDS Library",
                        "action": "navigate",
                        "url": f"/sds/upload?file_path={file_info.get('path', '')}",
                        "style": "primary"
                    },
                    {
                        "text": "Review Document First",
                        "action": "continue_conversation",
                        "message": "Let me review this document before adding it to the library"
                    }
                ],
                "guidance": "Our SDS library uses AI to make safety data sheets searchable and chattable. Once uploaded, you'll be able to ask questions like 'What PPE is required?' or 'What are the fire hazards?'"
            }
        else:
            return {
                "message": f"📄 **PDF Document Received: {filename}**\n\nI've received your PDF document. How would you like me to help you with this?",
                "type": "general_pdf",
                "actions": [
                    {
                        "text": "Add as SDS",
                        "action": "navigate",
                        "url": f"/sds/upload?file_path={file_info.get('path', '')}",
                        "style": "primary"
                    },
                    {
                        "text": "Attach to Incident",
                        "action": "continue_conversation",
                        "message": "I want to attach this document to an incident report"
                    },
                    {
                        "text": "Use for CAPA",
                        "action": "continue_conversation", 
                        "message": "This document contains information for a corrective action"
                    }
                ],
                "quick_replies": [
                    "This is a safety data sheet",
                    "This is incident documentation",
                    "This is a policy or procedure",
                    "Help me categorize this document"
                ]
            }

    def handle_document_upload(self, message: str, file_info: Dict, user_id: str) -> Dict:
        """Handle other document uploads"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        return {
            "message": f"📎 **Document Received: {filename}**\n\nI've received your document. Based on the context, how would you like me to help you with this file?",
            "type": "general_document",
            "actions": [
                {
                    "text": "Attach to Report",
                    "action": "continue_conversation",
                    "message": "I want to attach this to an incident or safety report"
                },
                {
                    "text": "Use for Documentation",
                    "action": "continue_conversation",
                    "message": "This is supporting documentation for compliance"
                },
                {
                    "text": "Process as Evidence",
                    "action": "continue_conversation",
                    "message": "This document is evidence for an investigation"
                }
            ],
            "quick_replies": [
                "This supports an incident report",
                "This is compliance documentation", 
                "This is training material",
                "Help me determine how to use this"
            ]
        }

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
        
        elif re.search(r"dashboard|overview|status|summary|what.*urgent|priority|attention", message):
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

    def show_dashboard_overview(self) -> Dict:
        """Show system overview and urgent items with current data"""
        
        try:
            # Load actual data
            urgent_items = self.get_urgent_items()
            stats = self.get_system_stats()
            
            message = f"**📊 System Overview**\n\n"
            
            if urgent_items:
                message += "**⚠️ Items Requiring Attention:**\n"
                for item in urgent_items[:3]:  # Show top 3 most urgent
                    urgency_emoji = "🔴" if item.get('days_overdue', 0) > 7 else "🟡"
                    message += f"{urgency_emoji} {item['type']}: {item['description']}\n"
                if len(urgent_items) > 3:
                    message += f"   ... and {len(urgent_items) - 3} more items\n"
                message += "\n"
            
            message += f"""**📈 Current Statistics:**
• 🚨 Open Incidents: **{stats.get('incidents', {}).get('open', 0)}**
• ⏰ Overdue CAPAs: **{stats.get('capas', {}).get('overdue', 0)}**
• 🛡️ Safety Concerns: **{stats.get('safety_concerns', {}).get('open', 0)}**
• ⚠️ High Risk Items: **{stats.get('risk_assessments', {}).get('high_risk', 0)}**

What would you like to work on?"""
            
            actions = []
            
            if urgent_items:
                actions.append({
                    "text": "🚨 Address Urgent Items",
                    "action": "continue_conversation",
                    "message": "Help me address the most urgent items first"
                })
            
            actions.extend([
                {
                    "text": "📝 Report New Incident",
                    "action": "continue_conversation",
                    "message": "I need to report a new incident"
                },
                {
                    "text": "🛡️ Submit Safety Concern", 
                    "action": "continue_conversation",
                    "message": "I want to report a safety concern"
                },
                {
                    "text": "📊 View Full Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ])
            
            return {
                "message": message,
                "type": "dashboard_overview",
                "actions": actions,
                "quick_replies": [
                    "What needs my attention today?",
                    "Show me overdue items",
                    "Create a new CAPA",
                    "Upload an SDS document"
                ]
            }
            
        except Exception as e:
            # Fallback response if data loading fails
            return {
                "message": "**📊 Smart EHS System Overview**\n\nHere's what I can help you with today:\n\n• 🚨 **Report incidents** and safety concerns\n• 📋 **Create and manage CAPAs**\n• 📊 **Conduct risk assessments**\n• 📄 **Find safety data sheets**\n• 🔍 **Review audit findings**\n• 👥 **Manage contractors** and visitors\n\nWhat would you like to work on?",
                "type": "fallback_overview",
                "actions": [
