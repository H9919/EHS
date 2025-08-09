# services/ehs_chatbot.py - Memory-optimized version for Render free plan
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Conditional imports with graceful fallbacks
try:
    # Only import SBERT if specifically enabled via environment variable
    if os.getenv("ENABLE_SBERT", "false").lower() == "true":
        from sentence_transformers import SentenceTransformer
        import numpy as np
        SBERT_AVAILABLE = True
    else:
        SBERT_AVAILABLE = False
        print("SBERT disabled to save memory - using rule-based classification only")
except ImportError:
    SBERT_AVAILABLE = False
    print("SBERT not available - using rule-based classification only")

class LightweightIntentClassifier:
    """Memory-efficient intent classifier using only rule-based patterns"""
    
    def __init__(self):
        # Comprehensive rule patterns (no ML models loaded)
        self.rule_patterns = {
            'incident_reporting': [
                r'report.*incident', r'incident.*report', r'workplace.*incident',
                r'accident', r'injury', r'hurt', r'injured', r'damaged', r'spill', 
                r'collision', r'crash', r'fall', r'slip', r'trip', r'cut', r'burn',
                r'emergency.*happened', r'something.*happened', r'need.*report.*incident',
                r'someone.*hurt', r'property.*damage', r'environmental.*spill',
                r'workplace.*accident', r'got.*hurt', r'was.*injured', r'broke.*\w+',
                r'chemical.*leak', r'equipment.*failed', r'safety.*incident'
            ],
            'safety_concern': [
                r'safety.*concern', r'unsafe.*condition', r'hazard', r'dangerous',
                r'near.*miss', r'almost.*accident', r'safety.*issue', r'concern.*about',
                r'worried.*about', r'observed.*unsafe', r'potential.*danger',
                r'safety.*observation', r'unsafe.*behavior', r'safety.*violation',
                r'close.*call', r'could.*have.*been', r'safety.*risk', r'not.*safe'
            ],
            'sds_lookup': [
                r'sds', r'safety.*data.*sheet', r'chemical.*info', r'material.*safety',
                r'find.*chemical', r'lookup.*chemical', r'chemical.*safety',
                r'msds', r'chemical.*properties', r'hazard.*information',
                r'chemical.*name', r'cas.*number', r'what.*chemical'
            ],
            'risk_assessment': [
                r'risk.*assessment', r'evaluate.*risk', r'risk.*analysis',
                r'how.*risky', r'what.*risk', r'assess.*risk', r'risk.*level',
                r'likelihood', r'severity', r'risk.*matrix', r'risk.*score'
            ],
            'capa_management': [
                r'corrective.*action', r'preventive.*action', r'capa',
                r'fix.*problem', r'prevent.*future', r'action.*plan', r'follow.*up',
                r'root.*cause', r'why.*happen', r'improvement', r'corrective',
                r'preventive', r'action.*item'
            ],
            'dashboard_overview': [
                r'dashboard', r'overview', r'status', r'what.*urgent', r'what.*needs.*attention',
                r'summary', r'what.*overdue', r'priorities', r'what.*should.*do',
                r'show.*me', r'urgent.*items'
            ]
        }
        
        # Weighted scoring for better accuracy
        self.pattern_weights = {
            'incident_reporting': {
                r'report.*incident': 0.95,
                r'workplace.*accident': 0.9,
                r'someone.*hurt': 0.85,
                r'injury': 0.8,
                r'accident': 0.7
            },
            'safety_concern': {
                r'safety.*concern': 0.95,
                r'unsafe.*condition': 0.9,
                r'near.*miss': 0.85,
                r'hazard': 0.8
            }
        }
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Lightweight rule-based classification with confidence scoring"""
        message_lower = message.lower().strip()
        
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        for intent, patterns in self.rule_patterns.items():
            intent_score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    matches += 1
                    # Use weighted scoring if available
                    weight = self.pattern_weights.get(intent, {}).get(pattern, 0.7)
                    intent_score = max(intent_score, weight)
            
            # Boost score for multiple matches
            if matches > 1:
                intent_score = min(0.95, intent_score + (matches - 1) * 0.1)
            
            if intent_score > best_confidence:
                best_confidence = intent_score
                best_intent = intent
        
        # Set minimum confidence threshold
        if best_confidence < 0.3:
            return 'general_inquiry', 0.3
        
        return best_intent, best_confidence

class MemoryEfficientSlotPolicy:
    """Lightweight slot filling without heavy data structures"""
    
    def __init__(self):
        # Minimal slot definitions
        self.incident_slots = {
            'injury': ['description', 'location', 'injured_person', 'injury_type', 'body_part', 'severity'],
            'vehicle': ['description', 'location', 'vehicles_involved', 'damage_estimate', 'injuries'],
            'environmental': ['description', 'location', 'chemical_name', 'spill_volume', 'containment'],
            'near_miss': ['description', 'location', 'potential_consequences'],
            'property': ['description', 'location', 'damage_description', 'estimated_cost'],
            'other': ['description', 'location', 'incident_details']
        }
        
        # Minimal question templates
        self.questions = {
            'description': "Please describe what happened in detail:",
            'location': "Where did this occur? (Building, area, specific location)",
            'injured_person': "Who was involved? (Name or 'Anonymous')",
            'injury_type': "What type of injury occurred?",
            'body_part': "Which body part was affected?",
            'severity': "How severe was the injury?",
            'chemical_name': "What chemical was involved?",
            'spill_volume': "How much was spilled?",
            'vehicles_involved': "Which vehicles were involved?",
            'damage_estimate': "Estimated damage cost?",
            'potential_consequences': "What could have happened?"
        }

class LightweightEHSChatbot:
    """Memory-optimized chatbot for Render free plan"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_mode = 'general'
        self.current_context = {}
        self.slot_filling_state = {}
        
        # Use lightweight components
        self.intent_classifier = LightweightIntentClassifier()
        self.slot_policy = MemoryEfficientSlotPolicy()
        
        print("Lightweight EHS Chatbot initialized (rule-based only)")
    
    def process_message(self, user_message: str, user_id: str = None, context: Dict = None) -> Dict:
        """Process message with minimal memory usage"""
        context = context or {}
        user_id = user_id or "default_user"
        
        # Handle file uploads
        uploaded_file = context.get("uploaded_file")
        if uploaded_file:
            return self.handle_file_upload(user_message, uploaded_file, context)
        
        # Emergency detection (highest priority)
        if self.is_emergency(user_message):
            return self.handle_emergency()
        
        # Intent classification
        intent, confidence = self.intent_classifier.classify_intent(user_message)
        
        # Mode switching
        if confidence > 0.6:  # Lower threshold for rule-based
            self.switch_mode(intent)
        
        # Process based on mode
        if self.current_mode == 'incident':
            response = self.process_incident_mode(user_message, intent, confidence)
        elif self.current_mode == 'safety_concern':
            response = self.process_safety_concern_mode(user_message)
        elif self.current_mode == 'sds_qa':
            response = self.process_sds_mode(user_message)
        else:
            response = self.process_general_mode(user_message, intent)
        
        # Store minimal conversation data
        self.conversation_history.append({
            "user": user_message[:200],  # Truncate to save memory
            "bot": response.get("message", "")[:200],
            "intent": intent,
            "timestamp": time.time()  # Use timestamp instead of datetime string
        })
        
        # Keep only last 20 exchanges to limit memory
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def switch_mode(self, intent: str):
        """Switch modes with minimal state"""
        mode_map = {
            'incident_reporting': 'incident',
            'safety_concern': 'safety_concern', 
            'sds_lookup': 'sds_qa'
        }
        
        new_mode = mode_map.get(intent, 'general')
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.current_context = {}
            self.slot_filling_state = {}
    
    def process_incident_mode(self, message: str, intent: str, confidence: float) -> Dict:
        """Lightweight incident processing"""
        
        # Detect incident type
        if 'incident_type' not in self.current_context:
            detected_type = self.detect_incident_type(message)
            if detected_type:
                self.current_context['incident_type'] = detected_type
                return self.start_slot_filling(detected_type)
            else:
                return self.ask_incident_type()
        
        # Continue slot filling
        return self.continue_slot_filling(message)
    
    def detect_incident_type(self, message: str) -> Optional[str]:
        """Simple incident type detection"""
        msg = message.lower()
        
        type_keywords = {
            'injury': ['injur', 'hurt', 'cut', 'burn', 'medical', 'hospital', 'first aid'],
            'vehicle': ['vehicle', 'car', 'truck', 'collision', 'crash'],
            'environmental': ['spill', 'chemical', 'leak', 'environmental'],
            'near_miss': ['near miss', 'almost', 'could have', 'close call'],
            'property': ['damage', 'broken', 'property', 'equipment']
        }
        
        for incident_type, keywords in type_keywords.items():
            if any(keyword in msg for keyword in keywords):
                return incident_type
        
        return None
    
    def start_slot_filling(self, incident_type: str) -> Dict:
        """Start collecting required information"""
        slots = self.slot_policy.incident_slots.get(incident_type, ['description', 'location'])
        
        if slots:
            first_slot = slots[0]
            self.slot_filling_state = {
                'slots': slots,
                'current_slot': first_slot,
                'filled': 0
            }
            
            question = self.slot_policy.questions.get(first_slot, f"Please provide {first_slot}:")
            
            return {
                "message": f"📝 **{incident_type.title()} Incident Report**\n\n{question}",
                "type": "slot_filling",
                "progress": f"Step 1 of {len(slots)}",
                "guidance": "I'll guide you through each required field."
            }
        
        return self.complete_incident_report()
    
    def continue_slot_filling(self, message: str) -> Dict:
        """Continue collecting information"""
        if not self.slot_filling_state:
            return self.complete_incident_report()
        
        current_slot = self.slot_filling_state.get('current_slot')
        slots = self.slot_filling_state.get('slots', [])
        filled = self.slot_filling_state.get('filled', 0)
        
        # Store answer
        if current_slot:
            self.current_context[current_slot] = message
            filled += 1
            self.slot_filling_state['filled'] = filled
        
        # Check if more slots needed
        if filled < len(slots):
            next_slot = slots[filled]
            self.slot_filling_state['current_slot'] = next_slot
            question = self.slot_policy.questions.get(next_slot, f"Please provide {next_slot}:")
            
            return {
                "message": f"✅ Got it.\n\n**Next:** {question}",
                "type": "slot_filling",
                "progress": f"Step {filled + 1} of {len(slots)}"
            }
        
        return self.complete_incident_report()
    
    def complete_incident_report(self) -> Dict:
        """Complete incident with basic risk assessment"""
        incident_id = f"INC-{int(time.time())}"
        
        # Simple risk assessment without ML
        risk_level = self.simple_risk_assessment()
        
        # Save incident data
        self.save_incident_data(incident_id, risk_level)
        
        return {
            "message": f"✅ **Incident Report Completed**\n\n**Incident ID:** `{incident_id}`\n\n**Risk Level:** {risk_level}\n\nYour incident has been recorded and assigned a unique ID.",
            "type": "incident_completed",
            "incident_id": incident_id,
            "actions": [
                {
                    "text": "📄 View Report",
                    "action": "navigate",
                    "url": f"/incidents/{incident_id}/edit"
                },
                {
                    "text": "📊 Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ]
        }
    
    def simple_risk_assessment(self) -> str:
        """Basic rule-based risk assessment"""
        description = self.current_context.get('description', '').lower()
        severity = self.current_context.get('severity', '').lower()
        incident_type = self.current_context.get('incident_type', '')
        
        # High risk indicators
        high_risk_words = ['severe', 'hospital', 'major', 'significant', 'fatality', 'serious']
        if any(word in description + severity for word in high_risk_words):
            return "High"
        
        # Low risk indicators  
        low_risk_words = ['minor', 'first aid', 'superficial', 'small', 'negligible']
        if any(word in description + severity for word in low_risk_words):
            return "Low"
        
        # Default based on incident type
        type_risk = {
            'injury': 'Medium',
            'environmental': 'Medium', 
            'vehicle': 'Medium',
            'near_miss': 'Low',
            'property': 'Low'
        }
        
        return type_risk.get(incident_type, 'Medium')
    
    def save_incident_data(self, incident_id: str, risk_level: str):
        """Save incident with minimal data structure"""
        try:
            incidents_file = Path("data/incidents.json")
            incidents_file.parent.mkdir(exist_ok=True)
            
            # Load existing incidents
            if incidents_file.exists():
                try:
                    incidents = json.loads(incidents_file.read_text())
                except:
                    incidents = {}
            else:
                incidents = {}
            
            # Create minimal incident record
            incident_data = {
                "id": incident_id,
                "type": self.current_context.get('incident_type', 'other'),
                "created_ts": time.time(),
                "status": "complete",
                "risk_level": risk_level,
                "answers": {
                    "people": self.current_context.get('description', '') + ' ' + 
                             self.current_context.get('injured_person', ''),
                    "environment": "N/A",
                    "cost": self.current_context.get('damage_estimate', 'N/A'), 
                    "legal": "To be determined",
                    "reputation": "Low impact expected"
                },
                "reported_via": "chatbot_lite"
            }
            
            incidents[incident_id] = incident_data
            incidents_file.write_text(json.dumps(incidents, indent=2))
            
        except Exception as e:
            print(f"Error saving incident: {e}")
    
    def ask_incident_type(self) -> Dict:
        """Ask for incident type selection"""
        return {
            "message": "🚨 **I'll help you report this incident.**\n\nWhat type of incident occurred?",
            "type": "incident_type_selection",
            "actions": [
                {
                    "text": "🩹 Injury/Medical",
                    "action": "continue_conversation",
                    "message": "This involves a workplace injury"
                },
                {
                    "text": "🚗 Vehicle Incident", 
                    "action": "continue_conversation",
                    "message": "This involves a vehicle accident"
                },
                {
                    "text": "🌊 Environmental Spill",
                    "action": "continue_conversation",
                    "message": "This involves a chemical spill"
                },
                {
                    "text": "⚠️ Near Miss",
                    "action": "continue_conversation",
                    "message": "This was a near miss incident"
                },
                {
                    "text": "💔 Property Damage",
                    "action": "continue_conversation", 
                    "message": "This involves property damage"
                }
            ]
        }
    
    def process_safety_concern_mode(self, message: str) -> Dict:
        """Handle safety concerns"""
        return {
            "message": "🛡️ **Safety Concern Noted**\n\nThank you for speaking up about safety! Let me direct you to our reporting system.",
            "type": "safety_concern",
            "actions": [
                {
                    "text": "📝 Report Safety Concern",
                    "action": "navigate",
                    "url": "/safety-concerns/new"
                },
                {
                    "text": "📞 Anonymous Report", 
                    "action": "navigate",
                    "url": "/safety-concerns/new?anonymous=true"
                }
            ]
        }
    
    def process_sds_mode(self, message: str) -> Dict:
        """Handle SDS requests"""
        return {
            "message": "📄 **I'll help you find Safety Data Sheets.**\n\nOur SDS library is searchable and includes basic Q&A functionality.",
            "type": "sds_qa",
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
    
    def process_general_mode(self, message: str, intent: str) -> Dict:
        """Handle general inquiries"""
        if intent == 'dashboard_overview':
            return self.get_dashboard_overview()
        else:
            return self.get_general_help_response()
    
    def get_dashboard_overview(self) -> Dict:
        """Get system overview without heavy data processing"""
        return {
            "message": "📊 **EHS System Overview**\n\nI can help you navigate to different areas:\n\n• 🚨 Report incidents and safety concerns\n• 📊 View dashboards and system status\n• 📄 Find safety data sheets\n• 🔄 Manage corrective actions\n\nWhat would you like to work on?",
            "type": "dashboard_overview",
            "actions": [
                {
                    "text": "📊 View Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                },
                {
                    "text": "🚨 Report Incident",
                    "action": "continue_conversation",
                    "message": "I need to report a workplace incident"
                },
                {
                    "text": "📄 Find SDS", 
                    "action": "navigate",
                    "url": "/sds"
                }
            ]
        }
    
    def handle_file_upload(self, message: str, file_info: Dict, context: Dict) -> Dict:
        """Handle file uploads efficiently"""
        filename = file_info.get("filename", "")
        file_type = file_info.get("type", "")
        
        if file_type.startswith('image/'):
            return {
                "message": f"📸 **Image received: {filename}**\n\nI can help you use this image for incident reporting or safety documentation.",
                "type": "image_upload",
                "actions": [
                    {
                        "text": "🚨 Use for Incident Report",
                        "action": "navigate",
                        "url": "/incidents/new"
                    },
                    {
                        "text": "🛡️ Use for Safety Concern",
                        "action": "navigate", 
                        "url": "/safety-concerns/new"
                    }
                ]
            }
        elif file_type == 'application/pdf':
            return {
                "message": f"📄 **PDF received: {filename}**\n\nThis could be a Safety Data Sheet or important documentation.",
                "type": "pdf_upload",
                "actions": [
                    {
                        "text": "📋 Add to SDS Library",
                        "action": "navigate",
                        "url": "/sds/upload"
                    }
                ]
            }
        
        return {
            "message": f"📎 **File received: {filename}**\n\nHow would you like to use this file?",
            "type": "general_upload"
        }
    
    def is_emergency(self, message: str) -> bool:
        """Detect emergency situations"""
        emergency_words = [
            "emergency", "911", "fire", "bleeding", "unconscious", 
            "heart attack", "severe injury", "immediate danger"
        ]
        return any(word in message.lower() for word in emergency_words)
    
    def handle_emergency(self) -> Dict:
        """Emergency response"""
        return {
            "message": "🚨 **EMERGENCY DETECTED** 🚨\n\n**FOR LIFE-THREATENING EMERGENCIES:**\n📞 **CALL 911 IMMEDIATELY**\n\n**Site Emergency Contacts:**\n• Site Emergency: (555) 123-4567\n• Security: (555) 123-4568\n• EHS Hotline: (555) 123-4569",
            "type": "emergency",
            "actions": [
                {
                    "text": "📝 Report Emergency Incident",
                    "action": "navigate",
                    "url": "/incidents/new?type=emergency"
                }
            ]
        }
    
    def get_general_help_response(self) -> Dict:
        """General help response"""
        return {
            "message": "🤖 **I'm your EHS Assistant!**\n\nI can help you with:\n\n• 🚨 Report incidents and safety concerns\n• 📊 Navigate the EHS system\n• 📄 Find safety data sheets\n• 🔄 Get guidance on procedures\n\nWhat would you like to work on?",
            "type": "help_menu",
            "actions": [
                {
                    "text": "🚨 Report Incident",
                    "action": "continue_conversation",
                    "message": "I need to report a workplace incident"
                },
                {
                    "text": "🛡️ Safety Concern", 
                    "action": "continue_conversation",
                    "message": "I want to report a safety concern"
                },
                {
                    "text": "📊 View Dashboard",
                    "action": "navigate",
                    "url": "/dashboard"
                }
            ]
        }
    
    def get_conversation_summary(self) -> Dict:
        """Get lightweight conversation summary"""
        return {
            "message_count": len(self.conversation_history),
            "current_mode": self.current_mode,
            "timestamp": time.time(),
            "memory_efficient": True
        }

# Create the chatbot instance
def create_chatbot():
    """Factory function to create appropriate chatbot instance"""
    try:
        return LightweightEHSChatbot()
    except Exception as e:
        print(f"Error creating chatbot: {e}")
        return None
